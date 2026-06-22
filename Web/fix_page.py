import re

with open('/Users/daoson/MyProject/MAT/Web/src/app/predict/page.tsx', 'r') as f:
    content = f.read()

# Remove the two local refs
content = content.replace('  const currentTaskIdRef = useRef<string | null>(null);\n', '')
content = content.replace('  const pendingWsMessagesRef = useRef<Record<string, any>>({});\n', '')

# Remove currentTaskIdRef reset
content = content.replace('    currentTaskIdRef.current = null;\n', '')

# Remove the condition setting it
content = content.replace("""
      if (res.data.status === "queued" && res.data.task_id) {
        currentTaskIdRef.current = res.data.task_id;
      } else if (res.data.status === "success" && res.data.result) {""", """
      if (res.data.status === "success" && res.data.result) {""")

# We should also remove the empty "if (res.data.status === 'queued' && res.data.task_id) {}" if it exists.
# Let's check page.tsx around line 60.
