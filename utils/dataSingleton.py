class DataSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._screen_size = None
            cls._fish_options = None
            cls._vocab_options = None
            cls._vocab_font = None
            cls._espeak_engine = None
        return cls._instance

    @property
    def window_size(self):
        return self._screen_size

    @window_size.setter
    def window_size(self, size):
        if isinstance(size, tuple) and len(size) == 2:
            self._screen_size = size
        else:
            raise ValueError("Screen size must be a tuple of two integers")

    @property
    def fish_options(self):
        return self._fish_options

    @fish_options.setter
    def fish_options(self, fish: list):
        self._fish_options = fish

    @property
    def vocab_options(self):
        return self._vocab_options

    @vocab_options.setter
    def vocab_options(self, vocab: list):
        self._vocab_options = vocab

    @property
    def vocab_font(self):
        return self._vocab_font

    @vocab_font.setter
    def vocab_font(self, font):
        self._vocab_font = font
    
    @property
    def espeak_engine(self):
        return self._espeak_engine

    @espeak_engine.setter
    def espeak_engine(self, eng):
        self._espeak_engine = eng
