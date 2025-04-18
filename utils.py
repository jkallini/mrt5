# utils.py
# Author: Julie Kallini

import torch
import json
from models.modeling_t5 import T5ForConditionalGeneration, T5Config
from models.modeling_mrt5 import MrT5ForConditionalGeneration, MrT5Config
from models.modeling_bpt5 import BPT5ForConditionalGeneration
from models.modeling_canine import CanineT5ForConditionalGeneration
from datasets import Dataset, IterableDataset
import time

# Change this path name to the path of the project
BASE_PATH = "/nlp/scr3/nlp/llms-in-llms/mrt5"
CHECKPOINT_PATH = f"{BASE_PATH}/models"
LM_DATASET_PATH = f"{BASE_PATH}/lm_datasets"
DIAGNOSTIC_DATASET_PATH = f"{BASE_PATH}/diagnostic_datasets"
FINETUNE_DATASET_PATH = f"{BASE_PATH}/finetune_datasets"

DIAGNOSTIC_TASKS = ['copy', 'vowel_removal',
                    'contextual_vowel_removal', 'merge_ABC']
LM_TASK = "span_corruption"
FINETUNE_TASKS = ['xnli', 'xquad', 'tydiqa']
CHAR_IIT_TASKS_AND_INFO = {
    'spelling_correction_contextual':
        {
            'splits': ['train', 'val', 'test_context_dependent', 'test_context_independent'],
            'input_seq_length': 64,
            'output_seq_length': 64,
        },
    'word_search':
        {
            'splits': ['train', 'val', 'test_oov', 'test_paraphrase', 'test_overlap', 'test_paraphrase_overlap'],
            'input_seq_length': 128,
            'output_seq_length': 16,
        }
}
CHAR_IIT_TASKS = list(CHAR_IIT_TASKS_AND_INFO.keys())

MODEL_ARCHITECTURES = ['T5', 'MrT5', 'LogSigmoidMrT5',
                       'DecoderBaselineT5', 'RandomT5', 'FixedT5',
                       'BPT5', 'CanineT5']


def check_weights(model):
    for name, param in model.named_parameters():
        if param.requires_grad:
            mean = torch.mean(param).item()
            std = torch.std(param).item()
            print(f"Layer: {name} | Mean: {mean:.6f} | Std: {std:.6f}")


def load_small_model(model_name, model_class, training_task, seed, ckpt, sigmoid_mask_scale=-10.0, log_sigmoid_deletion_threshold=-5.0, use_softmax1=False, delete_gate_layer=2):
    model_path = CHECKPOINT_PATH + \
        "/{}_architecture/{}/{}_seed{}/checkpoints/checkpoint-{}"
    model_path = model_path.format(
        model_class, training_task, model_name, seed, ckpt)
    if model_class == "T5":
        config = T5Config.from_pretrained("google/byt5-small")
    elif model_class == "MrT5":
        config = MrT5Config.from_pretrained(
            "google/byt5-small", deletion_type="scaled_sigmoid", sigmoid_mask_scale=sigmoid_mask_scale, use_softmax1=use_softmax1, delete_gate_layer=delete_gate_layer)
    elif model_class == "LogSigmoidMrT5":
        config = MrT5Config.from_pretrained(
            "google/byt5-small", deletion_type="log_sigmoid", deletion_threshold=log_sigmoid_deletion_threshold, use_softmax1=use_softmax1, delete_gate_layer=delete_gate_layer)
    config.d_ff = 1024                                  # Feed-forward size
    config.d_model = 512                                # Hidden size
    config.num_layers = 9                               # Encoder layers
    config.num_decoder_layers = 3                       # Decoder layers
    config.has_absolute_position_embeddings = False     # Absolute position embeddings

    if model_class == "T5":
        model = T5ForConditionalGeneration.from_pretrained(
            model_path, config=config)
    else:
        model = MrT5ForConditionalGeneration.from_pretrained(
            model_path, config=config)
    return model


def load_model_from_scratch(model_class, config):
    if model_class in ('T5', 'DecoderBaselineT5'):
        model = T5ForConditionalGeneration(config=config)
    elif model_class == "MrT5":
        config.deletion_type = "scaled_sigmoid"
        model = MrT5ForConditionalGeneration(config=config)
    elif model_class == "LogSigmoidMrT5":
        config.deletion_type = "log_sigmoid"
        model = MrT5ForConditionalGeneration(config=config)
    elif model_class == "RandomT5":
        config.deletion_type = "random"
        model = MrT5ForConditionalGeneration(config=config)
    elif model_class == "FixedT5":
        config.deletion_type = "fixed"
        model = MrT5ForConditionalGeneration(config=config)
    else:
        raise ValueError(
            f"Model type must be one of {', '.join(MODEL_ARCHITECTURES)}.")

    return model


def load_model_from_path(model_class, model_path=None, model_name=None, training_task=None, seed=None, ckpt=None):
    if model_path is None:
        model_path = CHECKPOINT_PATH + \
            "/{}/{}/{}_seed{}/checkpoints/checkpoint-{}"
        print(training_task)
        model_path = model_path.format(
            training_task, model_class, model_name, seed, ckpt)

    print(f"Path: {model_path}")
    if model_class in ('T5', 'DecoderBaselineT5'):
        model = T5ForConditionalGeneration.from_pretrained(model_path)
    elif model_class == "MrT5":
        model = MrT5ForConditionalGeneration.from_pretrained(model_path)
    elif model_class == "LogSigmoidMrT5":
        model = MrT5ForConditionalGeneration.from_pretrained(model_path)
    elif model_class == "RandomT5":
        model = MrT5ForConditionalGeneration.from_pretrained(model_path)
    elif model_class == "FixedT5":
        model = MrT5ForConditionalGeneration.from_pretrained(model_path)
    elif model_class == "BPT5":
        model = BPT5ForConditionalGeneration.from_pretrained(model_path)
    elif model_class == "CanineT5":
        model = CanineT5ForConditionalGeneration.from_pretrained(model_path)
    else:
        raise ValueError(
            f"Model type must be one of {', '.join(MODEL_ARCHITECTURES)}.")
    return model


def load_model_from_hf(model_class, model_name, config):
    if model_class in ('T5', 'DecoderBaselineT5'):
        model = T5ForConditionalGeneration.from_pretrained(
            model_name, config=config)
    elif model_class == "MrT5":
        config.deletion_type = "scaled_sigmoid"
        model = MrT5ForConditionalGeneration.from_pretrained(
            model_name, config=config)
    elif model_class == "LogSigmoidMrT5":
        config.deletion_type = "log_sigmoid"
        model = MrT5ForConditionalGeneration.from_pretrained(
            model_name, config=config)
    elif model_class == "RandomT5":
        config.deletion_type = "random"
        model = MrT5ForConditionalGeneration.from_pretrained(
            model_name, config=config)
    elif model_class == "FixedT5":
        config.deletion_type = "fixed"
        model = MrT5ForConditionalGeneration.from_pretrained(
            model_name, config=config)
    elif model_class == "BPT5":
        model = BPT5ForConditionalGeneration.from_pretrained(
            model_name, config=config)
    elif model_class == "CanineT5":
        model = CanineT5ForConditionalGeneration.from_pretrained(
            model_name, config=config)
    else:
        raise ValueError(
            f"Model type must be one of {', '.join(MODEL_ARCHITECTURES)}.")

    return model


def load_processed_dataset(filename):
    with open(filename, 'r') as f:
        for line in f:
            yield json.loads(line)


def get_task_dataset(training_task, split, language="en", iterable_dataset=True):
    # Format the dataset path based on the training task
    if training_task == LM_TASK:
        dataset_path = LM_DATASET_PATH + \
            "/mc4-{}-{}.json".format(language, "{}")
    elif training_task == LM_TASK + "_multilingual":
        dataset_path = LM_DATASET_PATH + \
            "/mc4-multilingual-train.json" if split == "train" else LM_DATASET_PATH + \
            "/mc4-en-{}.json".format(split)
    elif training_task in CHAR_IIT_TASKS:
        dataset_path = FINETUNE_DATASET_PATH + "/char_iit_json/{}/{}_{}.json".format(
            training_task, training_task, "{}")
    else:
        dataset_path = DIAGNOSTIC_DATASET_PATH + "/diagnostic-{}-{}.json".format(
            training_task, "{}")

    # Load the processed datasets from files as generators
    def dataset_gen(): return load_processed_dataset(dataset_path.format(split))

    # Use Dataset.from_generator to create Dataset objects
    if iterable_dataset:
        dataset = IterableDataset.from_generator(dataset_gen)
    else:
        dataset = Dataset.from_generator(dataset_gen)

    return dataset

def calculate_seq_accuracy(labels, outputs):
    logits = outputs.logits
    # Get the predicted IDs
    predicted_ids = torch.argmax(logits, dim=-1)

    # Don't count indices of pad tokens as incorrect predictions
    pad_tokens = labels <= 0
    correct_tokens = (predicted_ids == labels) | pad_tokens

    # Compare predicted_ids with the true labels
    correct_predictions = correct_tokens.all(dim=-1).sum().item()
    total_predictions = labels.shape[0]

    # Calculate accuracy
    accuracy = correct_predictions / total_predictions

    return accuracy

def calculate_token_accuracy(labels, outputs):
    logits = outputs.logits
    # Get the predicted IDs
    predicted_ids = torch.argmax(logits, dim=-1)

    # Don't count indices of pad tokens as incorrect predictions
    pad_tokens = labels <= 0
    num_pad_tokens = pad_tokens.sum().item()

    # Compare predicted_ids with the true labels
    correct_tokens = (predicted_ids == labels) | pad_tokens

    # Compare predicted_ids with the true labels
    correct_predictions = correct_tokens.sum().item() - num_pad_tokens

    # Calculate accuracy
    total_predictions = labels.numel() - num_pad_tokens
    accuracy = correct_predictions / total_predictions

    return accuracy


def measure_runtime(model, input_ids, labels, num_passes=5, attention_mask=None, hard_delete=None, deletion_threshold=None):

    model_inputs = {
        "input_ids": input_ids,
        "labels": labels,
        "attention_mask": attention_mask,
    }

    if hard_delete is not None:
        model_inputs["hard_delete"] = hard_delete
        model_inputs["deletion_threshold"] = deletion_threshold

    # Ensure synchronization before timing the forward pass
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    batch_start = time.perf_counter()

    # Only time the model's forward pass
    for _ in range(num_passes):
        model(**model_inputs)

    if torch.cuda.is_available():
        torch.cuda.synchronize()
    batch_end = time.perf_counter()

    # Time taken ONLY for model inference
    return (batch_end - batch_start) / num_passes


def measure_runtime_generate(model, input_ids, num_passes=5, hard_delete=None, deletion_threshold=None):

    model_inputs = {
        "input_ids": input_ids,
        "max_length": 1024,
    }

    if hard_delete is not None:
        model_inputs["hard_delete"] = hard_delete
        model_inputs["deletion_threshold"] = deletion_threshold

    # Ensure synchronization before timing the forward pass
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    batch_start = time.perf_counter()

    # Only time the model's forward pass
    for _ in range(num_passes):
        model.generate(**model_inputs)

    if torch.cuda.is_available():
        torch.cuda.synchronize()
    batch_end = time.perf_counter()

    # Time taken ONLY for model inference
    return (batch_end - batch_start) / num_passes


def byt5_compute_metrics(model, input_ids, labels, attention_mask=None, include_runtime=False):

    # Set pad tokens to -100 so they are not counted in the loss
    labels[labels == 0] = -100

    # Get model outputs
    outputs = model(input_ids=input_ids,
                    labels=labels,
                    output_hidden_states=True,
                    attention_mask=attention_mask)
    
    # Calculate sequence and token accuracy
    seq_accuracy = calculate_seq_accuracy(labels, outputs)
    token_accuracy = calculate_token_accuracy(labels, outputs)

    # Get the new sequence length
    new_seq_length = outputs.encoder_last_hidden_state.shape[1]

    # Only time the model's forward pass
    if include_runtime:
        model_runtime = measure_runtime(model, input_ids=input_ids, labels=labels, attention_mask=attention_mask)
    else:
        model_runtime = 0.0

    return outputs.loss.item(), 0.0, new_seq_length, \
        seq_accuracy, token_accuracy, model_runtime


def mrt5_compute_metrics(model, input_ids, labels, deletion_threshold, hard_delete=True, attention_mask=None, include_runtime=False):

    # Set pad tokens to -100 so they are not counted in the loss
    labels[labels == 0] = -100

    # Get model outputs
    outputs = model(
        input_ids=input_ids,
        labels=labels,
        hard_delete=hard_delete,
        output_hidden_states=True,
        deletion_threshold=deletion_threshold,
        attention_mask=attention_mask)

    # Get delete gate output
    delete_gate_output = outputs.delete_gate_output.squeeze(-1)

    # Compute percent deleted tokens (excluding padding tokens)
    non_pad_mask = input_ids != 0
    num_non_pad_tokens = non_pad_mask.sum()
    num_deleted_tokens = ((delete_gate_output < deletion_threshold) & non_pad_mask).sum()
    percent_deleted_tokens = num_deleted_tokens / num_non_pad_tokens * 100

    # Calculate sequence and token accuracy
    seq_accuracy = calculate_seq_accuracy(labels, outputs)
    token_accuracy = calculate_token_accuracy(labels, outputs)

    # Get the new sequence length
    new_seq_length = outputs.encoder_last_hidden_state.shape[1]

    if include_runtime:
        # Only time the model's forward pass
        model_runtime = measure_runtime(
            model,
            input_ids=input_ids,
            labels=labels,
            hard_delete=hard_delete,
            deletion_threshold=deletion_threshold,
            attention_mask=attention_mask)
    else:
        model_runtime = 0.0

    # Return cross entropy loss, accuracy, and percent deleted tokens
    return outputs.loss.item(), percent_deleted_tokens.item(), \
        new_seq_length, seq_accuracy, token_accuracy, model_runtime


def bpt5_compute_metrics(model, input_ids, labels, attention_mask=None, include_runtime=False):

    # Set pad tokens to -100 so they are not counted in the loss
    labels[labels == 0] = -100

    # Get model outputs
    outputs = model(
        input_ids=input_ids,
        labels=labels,
        output_hidden_states=True,
        attention_mask=attention_mask)

    # Count on average how many tokens are deleted
    hard_boundaries = outputs.hard_boundaries
    batch_size, seq_len = input_ids.shape[0:2]
    num_deleted_tokens = torch.sum(hard_boundaries < 1.0).item()
    percent_deleted_tokens = num_deleted_tokens / (batch_size * seq_len) * 100

    # Calculate sequence and token accuracy
    seq_accuracy = calculate_seq_accuracy(labels, outputs)
    token_accuracy = calculate_token_accuracy(labels, outputs)

    # Get the new sequence length
    new_seq_length = outputs.encoder_last_hidden_state.shape[1]

    if include_runtime:
        # Only time the model's forward pass
        model_runtime = measure_runtime(model, input_ids=input_ids, labels=labels, attention_mask=attention_mask)
    else:
        model_runtime = 0.0

    # Return cross entropy loss, accuracy, and percent deleted tokens
    return outputs.loss.item(), percent_deleted_tokens, \
        new_seq_length, seq_accuracy, token_accuracy, model_runtime


def canine_compute_metrics(model, input_ids, labels, attention_mask=None, include_runtime=False):

    # Set pad tokens to -100 so they are not counted in the loss
    labels[labels == 0] = -100

    # Get model outputs
    outputs = model(
        input_ids=input_ids,
        labels=labels,
        output_hidden_states=True,
        attention_mask=attention_mask)

    # Count on average how many tokens are deleted
    _, seq_len = input_ids.shape[0:2]
    percent_deleted_tokens = (1.0 - outputs.encoder_last_hidden_state.shape[1] / \
            seq_len) * 100

    # Calculate sequence and token accuracy
    seq_accuracy = calculate_seq_accuracy(labels, outputs)
    token_accuracy = calculate_token_accuracy(labels, outputs)

    # Get the new sequence length
    new_seq_length = outputs.encoder_last_hidden_state.shape[1]

    # Only time the model's forward pass
    if include_runtime:
        model_runtime = measure_runtime(model, input_ids=input_ids, labels=labels, attention_mask=attention_mask)
    else:
        model_runtime = 0.0

    # Return cross entropy loss, accuracy, and percent deleted tokens
    return outputs.loss.item(), percent_deleted_tokens, \
        new_seq_length, seq_accuracy, token_accuracy, model_runtime


ALL_LANGUAGES = {
    "af": "Afrikaans",
    "am": "Amharic",
    "ar": "Arabic",
    "az": "Azerbaijani",
    "be": "Belarusian",
    "bg": "Bulgarian",
    "bg-Latn": "Bulgarian (Latin)",
    "bn": "Bangla",
    "ca": "Catalan",
    "ceb": "Cebuano",
    "co": "Corsican",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "el-Latn": "Greek (Latin)",
    "en": "English",
    "eo": "Esperanto",
    "es": "Spanish",
    "et": "Estonian",
    "eu": "Basque",
    "fa": "Persian",
    "fi": "Finnish",
    "fil": "Filipino",
    "fr": "French",
    "fy": "Western Frisian",
    "ga": "Irish",
    "gd": "Scottish Gaelic",
    "gl": "Galician",
    "gu": "Gujarati",
    "ha": "Hausa",
    "haw": "Hawaiian",
    "hi": "Hindi",
    "hi-Latn": "Hindi (Latin script)",
    "hmn": "Hmong, Mong",
    "ht": "Haitian",
    "hu": "Hungarian",
    "hy": "Armenian",
    "id": "Indonesian",
    "ig": "Igbo",
    "is": "Icelandic",
    "it": "Italian",
    "iw": "former Hebrew",
    "ja": "Japanese",
    "ja-Latn": "Japanese (Latin)",
    "jv": "Javanese",
    "ka": "Georgian",
    "kk": "Kazakh",
    "km": "Khmer",
    "kn": "Kannada",
    "ko": "Korean",
    "ku": "Kurdish",
    "ky": "Kyrgyz",
    "la": "Latin",
    "lb": "Luxembourgish",
    "lo": "Lao",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mg": "Malagasy",
    "mi": "Maori",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "mr": "Marathi",
    "ms": "Malay",
    "mt": "Maltese",
    "my": "Burmese",
    "ne": "Nepali",
    "nl": "Dutch",
    "no": "Norwegian",
    "ny": "Nyanja",
    "pa": "Punjabi",
    "pl": "Polish",
    "ps": "Pashto",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "ru-Latn": "Russian (Latin)",
    "sd": "Sindhi",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sm": "Samoan",
    "sn": "Shona",
    "so": "Somali",
    "sq": "Albanian",
    "sr": "Serbian",
    "st": "Southern Sotho",
    "su": "Sundanese",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "tg": "Tajik",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "xh": "Xhosa",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "zh": "Chinese",
    "zh-Latn": "Chinese (Latin)",
    "zu": "Zulu"
}


SUBSET_LANGUAGES = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "el": "Greek",
    "bg": "Bulgarian",
    "ru": "Russian",
    "tr": "Turkish",
    "ar": "Arabic",
    "vi": "Vietnamese",
    "th": "Thai",
    "zh": "Chinese",
    "hi": "Hindi",
    "sw": "Swahili",
    "ur": "Urdu",
}

XNLI_LANGUAGES = SUBSET_LANGUAGES

XQUAD_LANGUAGES = {
    "ar": "Arabic",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "hi": "Hindi",
    "ru": "Russian",
    "th": "Thai",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "zh": "Chinese",
    "ro": "Romanian",
}

TYDIQA_LANGUAGES = {
    "ru": "Russian",
    "ar": "Arabic",
    "bn": "Bengali",
    "te": "Telugu",
    "fi": "Finnish",
    "sw": "Swahili",
    "ko": "Korean",
    "id": "Indonesian",
    "en": "English",
}
