from voice_assistant.tts.streaming import sentence_chunks


def test_sentence_chunks_splits_on_punctuation():
    chunks = list(sentence_chunks("Hello. How are you? I'm fine!"))
    assert chunks == ["Hello.", "How are you?", "I'm fine!"]


def test_sentence_chunks_handles_streaming_input():
    """Feed the chunker token-by-token and verify it emits sentences only when complete."""
    from voice_assistant.tts.streaming import StreamingSentenceChunker
    s = StreamingSentenceChunker()
    out = []
    for piece in ["Hello", " there", ".", " How", " are", " you", "?"]:
        out.extend(s.feed(piece))
    out.extend(s.flush())
    assert out == ["Hello there.", "How are you?"]


def test_sentence_chunks_handles_no_terminal_punctuation():
    from voice_assistant.tts.streaming import StreamingSentenceChunker
    s = StreamingSentenceChunker()
    s.feed("This has no terminal punctuation")
    assert list(s.flush()) == ["This has no terminal punctuation"]
