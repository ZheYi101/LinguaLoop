"""Allow local materials and history to open without inventing offline replies."""


class UnavailableLearningLLMProvider:
    display_label = '本地资料 · AI 未配置'
    preparation_cache_identity = 'unavailable'
    supports_streaming = False
    offline_read_only = True

    async def _unavailable(self, **kwargs):
        raise RuntimeError('AI 服务尚未配置，本地材料和对话历史仍可查看。请在 .env 中配置 OPENAI_* 后重启。')

    analyze_material = generate_task = generate_reply = prepare_custom_topic = _unavailable
    prepare_dialogue = correct_answer = create_review_items = summarize_session = _unavailable
