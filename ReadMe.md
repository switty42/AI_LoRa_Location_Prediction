# AI LoRa Location Prediction
Docs 3-26-23 V1 (For questions or comments:  Stephen Witty switty@level500.com)  

### Project Overview:
The Helium LoRa network provides low-cost internet access for IoT devices.  In general, devices that require geographic location information include a GPS module.   This said while the Helium LoRa network has no native client device location information, the Helium LoRa hotspots are defined by latitude and longitude coordinates at installation time.  This information can be collected on every IoT LoRa transmission along with signal strength, SNR, etc, and used to calculate a rough position of any LoRa device without a GPS module.  If only a rough position is required, a device can be lower cost and have longer battery life by not requiring a GPS module.

This project is investigating the ability of an AI to determine the device position when provided with the known attributes of each LoRa communication.
### Many thanks:


- The Mycelium Networks Builder Program for support and encouragement
- @WW from Mycelium Networks for AI prompt advice

<img src="Pics/Mycelium.png" width="100">

### Approach:
- Initially using ChatGPT 3.5 as the AI
- A source LoRa data set has been collected from northwest AR.  For more information see this repository:  https://github.com/switty42/Red_October
- The data from each LoRa transmission is programmatically given to the AI via a Python interface.  
- The AI is asked to determine the transmitting device's position.
- The AI's position answer is then compared to the GPS data in the sample set.
- The distance error between the AI's answer and GPS is captured and averaged for the entire dataset.

### Reporting - The log file contains the following:
- Status about the dataset - distance, transmissions, etc.
- A rough estimate of misplaced Helium hotspots is calculated for information purposes.  This data is not provided to the AI model.
- Each LoRa transmission is started with an index number which ties it to the record position within the dataset
- The first couple of LoRa transmissions contain the text of the AI prompt.
- The response back from the AI is printed for each transmission.
- The distance error rate between GPS and the AI prediction is displayed.
- The entire dataset is looped through.
- At the end of the report, the average distance error for the entire dataset is displayed.
