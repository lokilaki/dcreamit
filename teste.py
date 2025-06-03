import re
import time


teste = int(re.search(r'(\d{2})\s*$', "TI_234857209348_01").group(1))
time.sleep(teste*10)