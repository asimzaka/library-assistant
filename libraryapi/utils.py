from sentence_transformers import SentenceTransformer
import numpy as np
from django.db import models

class BookVectorizer:
    def __init__(self):
        # Load a pre-trained model (you can choose an appropriate model)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Example model

    def generate_vector(self, title, description):
        # Combine title and description into one text
        text = f"{title} {description}"
        
        # Generate a vector using the model
        vector = self.model.encode(text)

        return vector

vectorizer = BookVectorizer()


from django.db.models import Func

# Assuming vector is stored as an array in PostgreSQL
class L2Distance(Func):
    function = 'sqrt'
    template = "(%(function)s(sum((vector - array[%(expressions)s]::float[]) * (vector - array[%(expressions)s]::float[])))::float)"
    output_field = models.FloatField()

def distance(vector1, vector2):
    return np.linalg.norm(vector1 - vector2)