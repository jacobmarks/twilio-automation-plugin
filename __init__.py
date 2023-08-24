"""Twilio Automation plugin.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

from datetime import datetime
import os

import fiftyone as fo
from fiftyone.core.utils import add_sys_path
import fiftyone.operators as foo
from fiftyone.operators import types
import fiftyone.core.utils as fou


twilio = fou.lazy_import("twilio")

from datetime import datetime
import os

with add_sys_path(os.path.dirname(os.path.abspath(__file__))):
    # pylint: disable=no-name-in-module,import-error
    from twilio_engine import *

def get_download_url(media_url):
    return f"https://{get_twilio_sid()}:{get_twilio_auth_token()}@{media_url.replace('https://', '')}"


def get_file_extension(media_type):
    if media_type == 'image/jpeg':
        return 'jpg'
    elif media_type == 'image/png':
        return 'png'
    elif media_type == 'video/mpeg':
        return 'mp4'
    else:
        raise ValueError(f"Unknown media type: {media_type}")


def get_local_basepath(dataset):
    if dataset.count() == 0:
        base_dir = "/tmp"
    else:
        path = dataset.first().filepath
        base_dir = "/".join(path.split("/")[:-1])
    return base_dir


def create_sample(media, message_body, message_sid, date_sent, local_basepath):
    """Create a FiftyOne sample from a Twilio message."""
    ext = get_file_extension(media.content_type)
    uri = media.uri
    local_filepath = os.path.join(local_basepath, media.sid + f".{ext}")
    media_url = 'https://api.twilio.com' + uri[:-5] # Strip off the '.json'
    download_url = get_download_url(media_url)

    ## Download the file
    os.system(f"wget {download_url} -O {local_filepath}")

    sample = fo.Sample(
        filepath=local_filepath,
        tags=["twilio"],
        message_body=message_body,
        message_sid=message_sid,
        date_sent=date_sent,
    )
    return sample


def add_twilio_samples(dataset, start_date=None, end_date=None):
    """Add Twilio samples to a FiftyOne dataset."""
    local_basepath = get_local_basepath(dataset)

    messages = get_twilio_messages()

    samples = []

    for message in messages:
        if int(message.num_media) > 0:
            body = message.body
            sid = message.sid
            date_sent = message.date_sent

            for media in message.media.list():
                sample = create_sample(media, body, sid, date_sent, local_basepath)
                samples.append(sample)

    if len(samples) > 0:
        dataset.add_samples(samples, dynamic=True)
    


class DownloadTwilioImages(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="add_twilio_images",
            label="Twilio Automation: download images from Twilio",
            dynamic=True,
            icon="/assets/twilio-icon.svg"
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        # if len(ctx.dataset) == 0:
        #     warning = types.Warning(
        #         label="Warning", description="The dataset is empty, so downloaded files will be stored in '/tmp.'"
        #     )
        #     inputs.view("warning", warning)

       

        # radio_choices = types.RadioGroup()
        # if replicate_flag:
        #     radio_choices.add_choice("sd", label="Stable Diffusion")
        #     radio_choices.add_choice("vqgan-clip", label="VQGAN-CLIP")
        # if openai_flag:
        #     radio_choices.add_choice("dalle2", label="DALL-E2")
        # inputs.enum(
        #     "model_choices",
        #     radio_choices.values(),
        #     default=radio_choices.choices[0].value,
        #     label="Models",
        #     view=radio_choices,
        # )

        # if ctx.params.get("model_choices", False) == "sd":
        #     size_choices = SD_SIZE_CHOICES
        #     width_choices = types.Dropdown(label="Width")
        #     for size in size_choices:
        #         width_choices.add_choice(size, label=size)

        #     inputs.enum(
        #         "width_choices",
        #         width_choices.values(),
        #         default="512",
        #         view=width_choices,
        #     )

        #     height_choices = types.Dropdown(label="Height")
        #     for size in size_choices:
        #         height_choices.add_choice(size, label=size)

        #     inputs.enum(
        #         "height_choices",
        #         height_choices.values(),
        #         default="512",
        #         view=height_choices,
        #     )

        #     inference_steps_slider = types.SliderView(
        #         label="Num Inference Steps",
        #         componentsProps={"slider": {"min": 1, "max": 500, "step": 1}},
        #     )
        #     inputs.int(
        #         "inference_steps", default=50, view=inference_steps_slider
        #     )

        #     scheduler_choices_dropdown = types.Dropdown(label="Scheduler")
        #     for scheduler in SD_SCHEDULER_CHOICES:
        #         scheduler_choices_dropdown.add_choice(
        #             scheduler, label=scheduler
        #         )

        #     inputs.enum(
        #         "scheduler_choices",
        #         scheduler_choices_dropdown.values(),
        #         default="K_EULER",
        #         view=scheduler_choices_dropdown,
        #     )

        # elif ctx.params.get("model_choices", False) == "dalle2":

        #     size_choices_dropdown = types.Dropdown(label="Size")
        #     for size in DALLE2_SIZE_CHOICES:
        #         size_choices_dropdown.add_choice(size, label=size)

        #     inputs.enum(
        #         "size_choices",
        #         size_choices_dropdown.values(),
        #         default="512x512",
        #         view=size_choices_dropdown,
        #     )

        # inputs.str("prompt", label="Prompt", required=True)
        return types.Property(inputs)

    def execute(self, ctx):
        dataset = ctx.dataset
        add_twilio_samples(dataset)




        # model_name = ctx.params.get("model_choices", "None provided")
        # model = get_model(model_name)
        # prompt = ctx.params.get("prompt", "None provided")
        # image_url = model.generate_image(ctx)

        # filename = generate_filepath(ctx.dataset)
        # download_image(image_url, filename)

        # sample = fo.Sample(
        #     filepath=filename,
        #     tags=["generated"],
        #     model=model.name,
        #     prompt=prompt,
        #     date_created=datetime.now(),
        # )
        # set_config(sample, ctx, model_name)

        # dataset = ctx.dataset
        # dataset.add_sample(sample, dynamic=True)

        if dataset.get_dynamic_field_schema() is not None:
            dataset.add_dynamic_sample_fields()
            ctx.trigger("reload_dataset")
        else:
            ctx.trigger("reload_samples")


def register(plugin):
    plugin.register(DownloadTwilioImages)
