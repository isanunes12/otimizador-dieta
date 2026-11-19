class LexicographicMethod:
    def __init__(self, w):
        self.w = w
    
    def __call__(self, model, f1, f2):
        model += self.w * f1 + (1-self.w) * f2