# change to model you want to download
from colpali_engine.models import ColQwen2, ColQwen2Processor

model_name = "vidore/colqwen2-v0.1"  # or whatever model you want to download


def first_time():
    model = ColQwen2.from_pretrained(
        model_name,
        cache_dir="models_hub/",  # where to save the model
        device_map="mps",  # Apple Silicon
    )

    processor = ColQwen2Processor.from_pretrained(model_name, cache_dir="models_hub/")
    return model, processor


def test_after_1st_time():
    model = ColQwen2.from_pretrained(
        model_name,
        local_files_only=True,
        cache_dir="models_hub/",
        device_map="mps",
    )
    processor = ColQwen2Processor.from_pretrained(
        model_name, local_files_only=True, cache_dir="models_hub/"
    )
    # it shoudln't download anything from the internet again
    return model, processor
