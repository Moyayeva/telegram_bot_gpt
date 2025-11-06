import tiktoken

class Tokenizer:
    def __init__(self, string:str, enc:str):
        self.string = string
        self.enc = enc

    def tokenize(self):
        encoding = tiktoken.get_encoding(self.enc)
        num_tokens = len(encoding.encode(self.string))
        return num_tokens
