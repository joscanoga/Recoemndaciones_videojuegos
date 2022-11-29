
import re
import numpy as np
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON

"""
Funciones a utilizar:
con read_data() se generan la matrix y el header.
los scores del usuairo se le entregan con el header original a build_user_vector(user_scores, header)
la recomendación se construye con recommend_games(matrix, user_vector, header), esta funcion retorna un diccionario con las recomendaciones.
"""

def build_user_vector(user_scores, header):
  indexes = []
  user_vector = np.zeros(len(header))
  for key, value in user_dictionary.items():
    indexes.append((np.where(np.array(header) == key)[0][0], value))
  for index, value in indexes:
    user_vector[index] = value
  return user_vector

def remove_decimal(x):
  result = float(x)
  while result > 1:
    result = result/10
  return round(result, 3)

def replacer_function(x):
  if re.match('(\d{1,2})\.?(\d{1,2})?\/(\d*)', x):
    result = round(eval(x),2)
  else:
    result = x
  return remove_decimal(result)

def fetch_data():
  sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
  sparql.setQuery("""
SELECT DISTINCT ?videogame ?videogameLabel ?reviewScore ?reviewByLabel
WHERE {
  ?videogame wdt:P31 wd:Q7889;
             wdt:P400 wd:Q1406;
             p:P444 ?review.
  ?review pq:P447 ?reviewBy;
          ps:P444 ?reviewScore.
  OPTIONAL{
    ?review ps:P400 ?Q16338.
  }
  MINUS {?review pq:P447 wd:Q21039459}
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en" .
  }
}
ORDER BY (?videogameLabel)
""")
  sparql.setReturnFormat(JSON)
  results = sparql.query().convert()
  result_matrix = []
  for result in results["results"]["bindings"]:
    result_matrix.append([result["videogameLabel"]["value"], result["reviewScore"]["value"], result["reviewByLabel"]["value"] ])
  df = pd.DataFrame(np.array(result_matrix), columns=['Videogame', 'Score', 'reviewdBy'])
  df.drop_duplicates( 
                    subset=['Videogame', 'reviewdBy'],
                    keep='first',
                    inplace=True)
  replacement_dict = {
    "A+":"100/100",
    "A":"95/100",
    "A-":"92.5/100",
    "B":"75/100",
    "B-":"67.5/100",
    "Essential":"100/100",
    "-/10":"1",
    "1+": "1"}
  df2 = df.copy()
  df2.Score.replace(replacement_dict, inplace=True)
  df2.Score = [e.replace(",",".").replace('%', '/100').replace("∞", "10").replace("Si on vous l’offre", "10").replace("☆ / Pending","0") for e in df2.Score]
  df2.Score = [e.replace("★★★★★", "5/5").replace("★★★★", "4/5").replace("PS5: ", "") for e in df2.Score]
  df2.Score = [re.sub(r'\s?\([\w\s-]+\)', "", e) for e in df2.Score]
  df2.Score = [re.sub(r'https?://www\.wikidata\.org/\.well-known/genid/\w+', "0", e) for e in df2.Score]
  df2.Score = [replacer_function(e) for e in df2.Score]
  df_pivot_raw = df2.pivot(index='reviewdBy', columns='Videogame')
  df_pivot_raw.columns = df_pivot_raw.columns.droplevel(0)
  df_pivot = df_pivot_raw.fillna(0)
  colab_matrix = df_pivot.to_numpy()
  head = list(df_pivot.columns)
  return (colab_matrix, head)

def read_data():
  try:
    matrix, header = fetch_data()
  except:
    matrix, header = read_from_txt()
  return matrix, header

def read_from_txt():
  matrix = np.load("./matrix.npy" ,allow_pickle=True)
  head = np.load("./head.npy" ,allow_pickle=True)
  return matrix, head

user_dictionary = {'Patrician IV': 0.3,
 'Getting Over It with Bennett Foddy': 0.4,
 'SCP-087': 0.45,
 'Sorority Rites': 0.7}
matrix, header = read_data()
user_vector = build_user_vector(user_dictionary, header)

def recommend_games(colaborative_matrix, user_vector, header, n_recommendations=3):
  # Conversión a numpy.
  user_vector = np.array(user_vector)
  colaborative_matrix = np.array(colaborative_matrix)
  # Fragmentación de la matriz en areas de interés.
  not_reviewed_games_indexes = np.where(user_vector == 0)[0]
  played_header = np.delete(header, not_reviewed_games_indexes)
  played_user = np.delete(user_vector, not_reviewed_games_indexes, axis=0)
  played_matrix = np.delete(colaborative_matrix, not_reviewed_games_indexes, axis=1)
  not_played_header = np.array(header)[not_reviewed_games_indexes]
  not_played_matrix = colaborative_matrix[:,not_reviewed_games_indexes]
  # Calculo de correlación usuario - Matriz colaborativa.
  correlation_coefs = np.corrcoef(played_matrix, played_user)[-1][:-1]
  np.nan_to_num(correlation_coefs, copy=False, nan=-0.9)
  # Calculo de la matriz de calificación con pesos.
  weighted_ratings_matrix = np.multiply(not_played_matrix, correlation_coefs[:, np.newaxis])
  rating_and_weight_matrix = np.sum(weighted_ratings_matrix, axis=0)
  matrix_of_ones = np.where(not_played_matrix!=0,1,0)
  corr_when_played = np.multiply(matrix_of_ones, correlation_coefs[:, np.newaxis])
  final_correlations = np.sum(corr_when_played, axis=0)
  # Vector de calificaciónes.
  final_vector = np.array([round(float(rating_and_weight_matrix[i]/final_correlations[i]), 3) for i in range(len(final_correlations))])
  #nans ocurren cuando se hace la división 0/0, por esto se reemplazan por 0
  np.nan_to_num(final_vector, copy=False, nan=0)
  #final_vector = np.divide(rating_and_weight_matrix, final_correlations)
  most_recommended_index = np.argpartition(final_vector, n_recommendations*-1)[n_recommendations*-1:]
  ordered_recommendation_indexes = np.flip(most_recommended_index[np.argsort(final_vector[most_recommended_index])])
  result_dict={}
  for index in ordered_recommendation_indexes:
    result_dict[not_played_header[index]] = final_vector[index]
  return result_dict

print(recommend_games(matrix, user_vector, header, 4))
