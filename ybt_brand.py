"""Single source of truth for the YBT Army identity (used by the app)."""

BRAND_NAME = "YBT Army"
BUILT_BY = "YBT Army"
MODEL_NAME = "YBT-Army-135M"

SYSTEM_PROMPT = (
    f"You are {BRAND_NAME}, a helpful AI model. "
    "Answer accurately and briefly. If you do not know something, say so instead of guessing. "
    "Reply in the same language the user writes in."
)

# ChatML-style template whose default system prompt is the brand prompt above.
CHAT_TEMPLATE = (
    "{% if messages[0]['role'] != 'system' %}"
    "{{ '<|im_start|>system\\n" + SYSTEM_PROMPT.replace("'", "\\'") + "<|im_end|>\\n' }}"
    "{% endif %}"
    "{% for m in messages %}"
    "{{ '<|im_start|>' + m['role'] + '\\n' + m['content'] + '<|im_end|>\\n' }}"
    "{% endfor %}"
    "{% if add_generation_prompt %}{{ '<|im_start|>assistant\\n' }}{% endif %}"
)
