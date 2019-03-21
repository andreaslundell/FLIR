# Torchlight
wget --post-data 'action=set&resource=.system.vcam.torch&value=true'  http://192.168.11.47/res.php

# Set mode
wget --post-data 'action=set&resource=.image.sysimg.fusion.fusionData.fusionMode&value=1'  http://192.168.11.47/res.php

# Measure in point 
wget --post-data 'action=get&resource=.image.sysimg.measureFuncs.spot.1.valueT'  http://192.168.11.47/res.php

