from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="meta-llama/Llama-3.1-8B-Instruct", 
    use_auth_token="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", 
    local_dir="E:\\marketxmind\\llama1B\\"
)
