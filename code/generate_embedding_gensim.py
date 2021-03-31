import os
import argparse
import pandas as pd
import numpy as np

from tqdm import tqdm
from gensim.models import Word2Vec

import data_loader
import data_path
import utils


def get_sentences(dataset):
    sentences = []
    for text in dataset.values():
        normalized_text = utils.normalize_text(text)
        words, _ = utils.tokenize_word_and_sentence(normalized_text, include_special_chars=True)
        sentences.append(words)
    return sentences


def embed_texts(model, sentences):
    embedded_texts = []
    for key, female_sentence in tqdm(sentences):
        embedded = np.zeros(vector_size)
        for word in female_sentence:
            embedded += model.wv[word]
        embedded /= len(female_sentence)

        embedded_dict = {}
        for i in range(len(embedded)):
            embedded_dict['F{}'.format(i)] = embedded[i]
        embedded_dict['number'] = key
        embedded_texts.append(embedded_dict)
    return pd.DataFrame(embedded_texts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Gensim Word Embedding Features')
    parser.add_argument('--data', type=str, default='../data/train/', help='path to dataset')
    parser.add_argument('--output', type=str, default='output', help='output name')
    parser.add_argument('--min-count', type=int, default=1, help='The minimum count of words to consider when training the model; words with occurrence less than this count will be ignored.')
    parser.add_argument('--vector-size', type=int, default=50, help='The number of dimensions of the embeddings')
    parser.add_argument('--window', type=int, default=5, help='The maximum distance between a target word and words around the target word.')
    parser.add_argument('--workers', type=int, default=3, help='The number of partitions during training.')
    parser.add_argument('--sg', type=int, default=1, help='The training algorithm, either CBOW(0) or skip gram(1).')
    parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()

    data = args.data
    model_path = os.path.join(data_path.MODEL_PATH, 'embedding_gensim.model')
    embedded_texts_path = os.path.join(data_path.DATA_PATH, '{}_embedded_texts_gensim.csv'.format(args.output))
    min_count = args.min_count
    vector_size = args.vector_size
    window = args.window
    workers = args.workers
    sg = args.sg
    verbose = args.verbose


    female_dataset = data_loader.load_dataset(data_path.FEMALE_DATA_PATH)
    male_dataset = data_loader.load_dataset(data_path.MALE_DATA_PATH)

    female_sentences_list = get_sentences(female_dataset)
    male_sentences_list = get_sentences(male_dataset)
    sentences = female_sentences_list + male_sentences_list

    if verbose:
        print('Train WordToVec for {} sentences: {} male, {} female ...'.format(len(sentences), len(female_sentences_list), len(male_sentences_list)))
    
    model = Word2Vec(sentences, min_count=min_count, vector_size=vector_size, window=window, workers=workers, sg=sg)
    model.save(model_path)

    if verbose:
        print('Model trained and saved in {}'.format(model_path))
        print('Embedding female dataset ...')

    female_embedded_texts = embed_texts(model, zip(female_dataset.keys(), female_sentences_list))
    female_embedded_texts['label'] = 0

    if verbose:
            print('Embedding male dataset ...')
    male_embedded_texts = embed_texts(model, zip(male_dataset.keys(), male_sentences_list))
    male_embedded_texts['label'] = 1

    embedded_text = pd.concat([female_embedded_texts, male_embedded_texts], axis=0)
    embedded_text.to_csv(embedded_texts_path)
    if verbose:
        print('Two dataset concatenate and saved in {} with shape {}.'.format(embedded_texts_path, embedded_text.shape))
    
