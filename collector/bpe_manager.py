from tokenizers import Tokenizer, models, trainers, pre_tokenizers
from typing import List

class BPEManager:
    def __init__(self, vocab_size: int = 1000):
        self.tokenizer = Tokenizer(models.BPE(unk_token="[UNK]"))
        # pre_tokenizer を指定しない場合、生の文字単位で処理される
        self.tokenizer.pre_tokenizer = None
        self.vocab_size = vocab_size
        self.trainer = trainers.BpeTrainer(
            vocab_size=vocab_size, 
            special_tokens=["[UNK]", "[PAD]", "[CLS]", "[SEP]", "[MASK]"]
        )

    def train(self, texts: List[str]):
        """与えられたテキストデータでBPEを学習する"""
        if not texts:
            return
        self.tokenizer.train_from_iterator(texts, trainer=self.trainer)

    def tokenize(self, text: str) -> List[str]:
        """テキストを現在の語彙でトークン化する"""
        encoding = self.tokenizer.encode(text)
        return encoding.tokens

    def get_vocab(self):
        return self.tokenizer.get_vocab()
