"""Install exact HAL calibration inputs and a Nougat-schema tablet audio policy."""
from pathlib import Path
import shutil

ROOT=Path('/root/t110-lineage14')
DEVICE=ROOT/'android/device/samsung/goyawifi'
STOCK=ROOT/'reference/stock-ani7/extracted'
policy='''# Nougat schema for the stock API2.0 primary HAL. Hardware routes are in audio_*XML.
global_configuration {
  attached_output_devices AUDIO_DEVICE_OUT_SPEAKER
  default_output_device AUDIO_DEVICE_OUT_SPEAKER
  attached_input_devices AUDIO_DEVICE_IN_BUILTIN_MIC|AUDIO_DEVICE_IN_REMOTE_SUBMIX
}
audio_hw_modules {
  primary {
    outputs {
      primary {
        sampling_rates 44100
        channel_masks AUDIO_CHANNEL_OUT_STEREO
        formats AUDIO_FORMAT_PCM_16_BIT
        devices AUDIO_DEVICE_OUT_SPEAKER|AUDIO_DEVICE_OUT_WIRED_HEADSET|AUDIO_DEVICE_OUT_WIRED_HEADPHONE|AUDIO_DEVICE_OUT_ALL_SCO
        flags AUDIO_OUTPUT_FLAG_PRIMARY
      }
    }
    inputs {
      primary {
        sampling_rates 8000|16000|44100|48000
        channel_masks AUDIO_CHANNEL_IN_MONO|AUDIO_CHANNEL_IN_STEREO
        formats AUDIO_FORMAT_PCM_16_BIT
        devices AUDIO_DEVICE_IN_BUILTIN_MIC|AUDIO_DEVICE_IN_WIRED_HEADSET|AUDIO_DEVICE_IN_BLUETOOTH_SCO_HEADSET
      }
    }
  }
  a2dp {
    outputs {
      a2dp {
        sampling_rates 44100|48000
        channel_masks AUDIO_CHANNEL_OUT_STEREO
        formats AUDIO_FORMAT_PCM_16_BIT
        devices AUDIO_DEVICE_OUT_ALL_A2DP
      }
    }
  }
  usb {
    outputs {
      usb_device {
        sampling_rates dynamic
        channel_masks dynamic
        formats dynamic
        devices AUDIO_DEVICE_OUT_USB_DEVICE|AUDIO_DEVICE_OUT_USB_ACCESSORY
      }
    }
    inputs {
      usb_device {
        sampling_rates dynamic
        channel_masks dynamic
        formats dynamic
        devices AUDIO_DEVICE_IN_USB_DEVICE|AUDIO_DEVICE_IN_USB_ACCESSORY
      }
    }
  }
  r_submix {
    outputs {
      submix {
        sampling_rates 48000
        channel_masks AUDIO_CHANNEL_OUT_STEREO
        formats AUDIO_FORMAT_PCM_16_BIT
        devices AUDIO_DEVICE_OUT_REMOTE_SUBMIX
      }
    }
    inputs {
      submix {
        sampling_rates 48000
        channel_masks AUDIO_CHANNEL_IN_STEREO
        formats AUDIO_FORMAT_PCM_16_BIT
        devices AUDIO_DEVICE_IN_REMOTE_SUBMIX
      }
    }
  }
}
'''
(DEVICE/'configs/audio_policy.conf').write_text(policy)
p=DEVICE/'device.mk';s=p.read_text()
lines=['\n# API2.0 primary HAL uses Nougat profiles, with original hardware calibration.\n',
       'PRODUCT_PACKAGES += audio.a2dp.default audio.usb.default\n',
       'PRODUCT_COPY_FILES += $(LOCAL_PATH)/configs/audio_policy.conf:system/etc/audio_policy.conf\n']
for source in sorted((STOCK/'etc').glob('audio_*.xml')):
    dest=DEVICE/'proprietary/etc'/source.name
    shutil.copy2(source,dest)
    lines.append('PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/'+source.name+':system/etc/'+source.name+'\n')
marker='# API2.0 primary HAL uses Nougat profiles, with original hardware calibration.'
if marker not in s:p.write_text(s+''.join(lines))
print('Installed seven original hardware audio XMLs and a Nougat API2.0 policy; runtime routes unqualified.')
