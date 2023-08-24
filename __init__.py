"""Twilio Automation plugin.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import os

import fiftyone as fo
import fiftyone.core.utils as fou
from fiftyone.core.utils import add_sys_path
import fiftyone.operators as foo
from fiftyone.operators import types
from fiftyone import ViewField as F

twilio = fou.lazy_import("twilio")


with add_sys_path(os.path.dirname(os.path.abspath(__file__))):
    # pylint: disable=no-name-in-module,import-error
    from twilio_engine import (
        get_twilio_sid,
        get_twilio_auth_token,
        get_twilio_messages,
    )


def get_download_url(media_url):
    return f"https://{get_twilio_sid()}:{get_twilio_auth_token()}@{media_url.replace('https://', '')}"


def get_file_extension(media_type):
    if media_type == "image/jpeg":
        return "jpg"
    elif media_type == "image/png":
        return "png"
    elif media_type == "video/mpeg":
        return "mp4"
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
    local_filepath = os.path.join(local_basepath, media.sid + f".{ext}")
    media_url = (
        "https://api.twilio.com" + media.uri[:-5]
    )  # Strip off the '.json'
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


def _has_sid(dataset, sid):
    if dataset.exists("message_sid").count() > 0:
        return dataset.match(F("message_sid") == sid).count() > 0
    return False


def add_twilio_samples(dataset, filter_text=None):
    """Add Twilio samples to a FiftyOne dataset."""
    local_basepath = get_local_basepath(dataset)

    messages = get_twilio_messages()

    samples = []

    for message in messages:
        if int(message.num_media) > 0:
            body = message.body
            sid = message.sid
            if _has_sid(dataset, sid):
                continue
            if filter_text is not None and filter_text not in body.lower():
                continue
            date_sent = message.date_sent

            for media in message.media.list():
                sample = create_sample(
                    media, body, sid, date_sent, local_basepath
                )
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
            icon="/assets/twilio-icon.svg",
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        if len(ctx.dataset) == 0:
            warning = types.Warning(
                label="Warning",
                description="The dataset is empty, so downloaded files will be stored in '/tmp.'",
            )
            inputs.view("warning", warning)

        inputs.message("message", label="Add Twilio images to your dataset!")

        inputs.bool(
            "filter",
            default=False,
            label="Filter by message content",
        )

        if ctx.params.get("filter", False):
            inputs.str(
                "filter_text",
                default="",
                label="Filter text",
                description="Only download images from messages that contain the given text:",
                required=True,
            )

        return types.Property(inputs)

    def execute(self, ctx):
        dataset = ctx.dataset
        add_twilio_samples(dataset, filter_text=ctx.params.get("filter_text"))

        if dataset.get_dynamic_field_schema() is not None:
            dataset.add_dynamic_sample_fields()
            ctx.trigger("reload_dataset")
        else:
            ctx.trigger("reload_samples")


def register(plugin):
    plugin.register(DownloadTwilioImages)
