import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class Book_similarity:

    def ngrams4(self, string, n=4):
        string = str(string)
        string = string.replace(" ","")
        string = string.replace("х","X")
        string = string.replace("Х","X")
        ngrams = zip(*[string[i:] for i in range(n)])
        return [''.join(ngram) for ngram in ngrams]

    def ngrams2(self, string, n=1):
        string = str(string)
        ngrams = zip(*[string[i:] for i in range(n)])
        return [''.join(ngram) for ngram in ngrams]

    def ngrams_for_column_mapping(self, string, n=3):
        string = str(string)
        ngrams = zip(*[string[i:] for i in range(n)])
        return [''.join(ngram) for ngram in ngrams]

    def get_cosine_similarity(self, input_string, isbns):
        vectorizer = TfidfVectorizer(analyzer=self.ngrams_for_column_mapping)
        matrix = vectorizer.fit_transform(isbns)
        tfidf_matrix_input = vectorizer.transform([input_string])

        similarity_scores = cosine_similarity(tfidf_matrix_input, matrix).flatten()

        return similarity_scores

    def get_cosine_similarity_for_single_vectors(self, first_string, second_string):
        vectorizer = TfidfVectorizer(analyzer=self.ngrams2)
        tfidf_matrix_second = vectorizer.fit_transform([second_string])
        tfidf_matrix_first = vectorizer.transform([first_string])

        similarity_scores = cosine_similarity(tfidf_matrix_second, tfidf_matrix_first)[0][0]

        return similarity_scores

    def get_matches_df(self, sparse_matrix, A, B, top=100):
        non_zeros = sparse_matrix.nonzero()

        sparserows = non_zeros[0]
        sparsecols = non_zeros[1]

        if top:
            nr_matches = top
        else:
            nr_matches = sparsecols.size

        left_side = np.empty([nr_matches], dtype=object)
        right_side = np.empty([nr_matches], dtype=object)
        similairity = np.zeros(nr_matches)

        for index in range(0, nr_matches):
            left_side[index] = A[sparserows[index]]
            right_side[index] = B[sparsecols[index]]
            similairity[index] = sparse_matrix.data[index]

        return pd.DataFrame({'left_side': left_side,
                            'right_side': right_side,
                            'similairity': similairity})

    def levenshteinDistanceDP(self, token1, token2):
        token1, token2 = str(token1), str(token2)
        distances = np.zeros((len(token1) + 1, len(token2) + 1))

        for t1 in range(len(token1) + 1):
            distances[t1][0] = t1

        for t2 in range(len(token2) + 1):
            distances[0][t2] = t2
            
        a = 0
        b = 0
        c = 0
        
        for t1 in range(1, len(token1) + 1):
            for t2 in range(1, len(token2) + 1):
                if (token1[t1-1] == token2[t2-1]):
                    distances[t1][t2] = distances[t1 - 1][t2 - 1]
                else:
                    a = distances[t1][t2 - 1]
                    b = distances[t1 - 1][t2]
                    c = distances[t1 - 1][t2 - 1]
                    
                    if (a <= b and a <= c):
                        distances[t1][t2] = a + 1
                    elif (b <= a and b <= c):
                        distances[t1][t2] = b + 1
                    else:
                        distances[t1][t2] = c + 1

        return distances[len(token1)][len(token2)]