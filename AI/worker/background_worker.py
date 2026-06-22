import asyncio
import uuid

from core.db import db
from services.rabbitmq_service import (
    rabbitmq,
    ROUTING_KEY_PREDICT_REQUESTS,
    ROUTING_KEY_PREDICT_RESULTS,
)

from training.router import ModelRouter


async def start_rabbitmq_worker(model_router: ModelRouter):
    """
    Hàm khởi động RabbitMQ Consumer độc lập.
    """

    async def process_ai_task_batch(payloads: list[dict]):
        batch_size = len(payloads)

        try:
            # QUAN TRỌNG: Đưa tác vụ AI nặng (CPU-Bound) ra Thread riêng
            results = await asyncio.to_thread(model_router.predict_batch, payloads)

            for output_message in results:
                await rabbitmq.publish_message(
                    output_message, routing_key=ROUTING_KEY_PREDICT_RESULTS
                )

            async def _save_to_db(res_list):
                # Insert predicted data into words_training
                db_args = []
                for msg in res_list:
                    if msg.get("status") == "success" and msg.get("ai_result"):
                        ai_res = msg["ai_result"]
                        comment = msg.get("original_text", "")
                        label = ai_res.get("label", "").lower()
                        score = ai_res.get("score")
                        segmented_text = ai_res.get("segmented_text", "")
                        model_used = ai_res.get("model_used", "")
                        if comment and label in ("positive", "negative", "neutral"):
                            db_args.append(
                                (
                                    uuid.uuid4(),
                                    comment,
                                    label,
                                    score,
                                    segmented_text,
                                    model_used,
                                )
                            )

                if db_args:
                    try:
                        await db.executemany(
                            """
                            INSERT INTO public.words_training 
                            (id, comment, label, score, segmented_text, model_used) 
                            VALUES ($1, $2, $3::public.sentiment_type, $4, $5, $6)
                            """,
                            db_args,
                        )
                    except Exception as db_err:
                        pass

            # Chạy lưu DB ở background, không block
            asyncio.create_task(_save_to_db(results))

        except Exception as e:
            for p in payloads:
                error_message = {
                    "task_id": p.get("task_id", "unknown"),
                    "original_text": p.get("text", ""),
                    "error": str(e),
                    "status": "failed",
                }
                await rabbitmq.publish_message(
                    error_message, routing_key=ROUTING_KEY_PREDICT_RESULTS
                )

    try:
        await rabbitmq.consume_messages_batch(
            queue_name=ROUTING_KEY_PREDICT_REQUESTS,
            batch_size=32,
            timeout=0.05,
            callback_function=process_ai_task_batch,
        )
    except asyncio.CancelledError:
        pass
    except Exception as e:
        pass
