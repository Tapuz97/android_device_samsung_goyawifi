"""Select standard ART at the deferred product-node evaluation point."""
from pathlib import Path
import subprocess

project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
repo=Path('/root/t110-build/lineage20/build/make')
file=repo/'target/product/runtime_libart.mk'
old='art_target_include_debug_build := $(PRODUCT_ART_TARGET_INCLUDE_DEBUG_BUILD)\n'
new=old+'''# inherit-product evaluates this node separately from the device product.
# Its parent PRODUCT_* setting is not available at this selection point.
# Keep eng debugging access but exclude the debug runtime on this legacy target.
ifeq (lineage_t110_system,$(TARGET_PRODUCT))
  art_target_include_debug_build := false
endif
'''
text=file.read_text()
assert text.count(old)==1 and new not in text
file.write_text(text.replace(old,new))
patch=subprocess.check_output(['git','-C',str(repo),'diff','--','target/product/runtime_libart.mk'])
(project/'patches/0043-build-t110-standard-art-selection.patch').write_bytes(patch)
subprocess.run(['git','-C',str(repo),'apply','--reverse','--check',str(project/'patches/0043-build-t110-standard-art-selection.patch')],check=True)
