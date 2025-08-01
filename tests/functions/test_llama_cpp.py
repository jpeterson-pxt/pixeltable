import platform

import pytest

import pixeltable as pxt

from ..utils import IN_CI, rerun, skip_test_if_not_installed, validate_update_status


# llama_cpp can be quite fussy, so we only run on Linux in CI environments.
@pytest.mark.skipif(
    IN_CI and platform.system() != 'Linux', reason='llama_cpp is unreliable in Windows/Mac CI environments.'
)
@rerun(reruns=3, reruns_delay=15)  # Since it involes a HF model download
class TestLlamaCpp:
    def test_create_chat_completions(self, reset_db: None) -> None:
        skip_test_if_not_installed('llama_cpp')
        from pixeltable.functions import llama_cpp

        t = pxt.create_table('test_tbl', {'input': pxt.String})

        t.add_computed_column(
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': t.input},
            ]
        )

        # We use a small model (~350MB) for testing.
        t.add_computed_column(
            output=llama_cpp.create_chat_completion(
                t.messages, repo_id='Qwen/Qwen2-0.5B-Instruct-GGUF', repo_filename='*q3_k_m.gguf'
            )
        )
        t.add_computed_column(
            output2=llama_cpp.create_chat_completion(
                t.messages,
                repo_id='Qwen/Qwen2-0.5B-Instruct-GGUF',
                repo_filename='*q3_k_m.gguf',
                model_kwargs={'max_tokens': 100, 'temperature': 0.7, 'top_p': 0.9, 'top_k': 20},
            )
        )

        validate_update_status(t.insert(input='What are some edible species of fish?'), expected_rows=1)
        result = t.collect()['output'][0]
        result2 = t.collect()['output2'][0]
        print(result)
        assert len(result['choices'][0]['message']['content']) > 0
        assert len(result2['choices'][0]['message']['content']) > 0

        llama_cpp.cleanup()  # Clean up the model cache after the test
