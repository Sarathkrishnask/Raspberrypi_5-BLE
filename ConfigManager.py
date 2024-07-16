"""
    File containing several utility methods that handle saving and loading of configuration files, and processing of command line arguments
"""
import yaml
import logging
import ntpath
import glob
import os
import numpy as np
from IStradaStateDef import DebugMode
from typing import TypeVar, Dict, Tuple

T = TypeVar('T')

curLogger = logging.getLogger("mainLogger")


def getConfigFileID(filePath):
    _, baseName = ntpath.split(filePath)
    baseName = baseName[:-5]
    baseNameSplit = baseName.split(".")

    if len(baseNameSplit) < 2:  # Then original file
        return 0
    else:
        version = baseNameSplit[-1]
        if version.isnumeric():
            return int(version)

        else:  # Probably the original file, but it contains a . in the middle.
            # It was not created in code, otherwise it would not fail this
            return 0


def importConfigFile(filePath):
    folderPath, baseName = ntpath.split(filePath)
    baseNameNoExt = baseName[:-5]

    configFiles = glob.glob(os.path.join(folderPath, baseNameNoExt + "*"))
    configFiles = sorted(configFiles)

    # Choose the latest config file
    # Extract IDs
    fileIDs = []
    for fileP in configFiles:
        fileIDs.append(getConfigFileID(fileP))

    sortedIdx = np.argsort(fileIDs)

    chosenConfigFile = filePath
    print(filePath)
    if len(fileIDs) > 1:
        curLogger.info("Detected multiple versions of the base configuration file. Picking the latest")
        curLogger.info("Latest File Path -> %s", configFiles[sortedIdx[-1]])
        chosenConfigFile = configFiles[sortedIdx[-1]]

    try:
        with open(chosenConfigFile) as file:
            # The FullLoader parameter handles the conversion from YAML
            # scalar values to Python the dictionary format
            controlOptions = yaml.load(file, Loader=yaml.FullLoader)
    except FileNotFoundError:
        curLogger.critical("Configuration file not found. Please check the file name and path.")
        exit()

    # Check on the device OS, in case it has been spelled wrongly
    controlOptions["serverInformation"]["deviceOS"] = controlOptions["serverInformation"]["deviceOS"].lower()
    if controlOptions["serverInformation"]["deviceOS"] not in ('android', 'ios'):
        curLogger.critical("OS specified for server communication is not a valid one. Please choose Android or iOS.")
        exit()

    return chosenConfigFile, controlOptions


def handleCommandLineInput(kwargs) -> Tuple[Dict[str, T], DebugMode]:
    cmdLineOptions = {}

    cmdLineOptions["timedExecution"] = False

    # Execution Duration
    if kwargs["executionDuration"] != 0:
        cmdLineOptions["timedExecution"] = True
        cmdLineOptions["runTime"] = kwargs["executionDuration"]

    if kwargs["inputVideoFile"] != "":
        cmdLineOptions["loadVideo"] = True
        cmdLineOptions["videoFilePath"] = kwargs["inputVideoFile"]
    else:
        cmdLineOptions["loadVideo"] = False

    # TODO Remove for final version
    cmdLineOptions["enableServerComm"] = kwargs["enableServerCommunication"]
    cmdLineOptions["enableGPIOReader"] = kwargs["enableWaterReader"]

    # Resolution
    resolutionArg = kwargs["resolution"]
    if resolutionArg in '1920x1080':
        cmdLineOptions["width"] = 1920
        cmdLineOptions["height"] = 1080
    elif resolutionArg in '1280x720':
        cmdLineOptions["width"] = 1280
        cmdLineOptions["height"] = 720
    elif resolutionArg in '640x480':
        cmdLineOptions["width"] = 640
        cmdLineOptions["height"] = 480
    else:
        curLogger.critical("Something is wrong with the provided resolution.")
        exit()

    # Frame rate
    cmdLineOptions["fps"] = kwargs["frameRate"]

    debugModeInfo = DebugMode()
    # Show Processing Rate
    # cmdLineOptions["showStepsFPS"] = kwargs["showProcessingRate"]
    debugModeInfo.showStepsFPS = kwargs["showProcessingRate"]

    # Show Debug Info
    # cmdLineOptions["showDebugInfo"] = kwargs["debug"]
    debugModeInfo.showDebugInfo = kwargs["debug"]

    # Draw Debug images
    # cmdLineOptions["drawDebugImages"] = kwargs["drawDebugImages"]
    debugModeInfo.drawDebugImages = kwargs["drawDebugImages"]

    # Save Fail Videos
    # cmdLineOptions["saveFailVideos"] = kwargs["saveFailScenarios"]
    debugModeInfo.saveFailVideos = kwargs["saveFailScenarios"]

    # Draw in real time instead of caching and waiting for the end to process
    # cmdLineOptions["drawRealTime"] = kwargs["drawRealTime"]
    debugModeInfo.drawRealTime = kwargs["drawRealTime"]

    return cmdLineOptions, debugModeInfo


def convertCommandLineOptions2ControlOptions(cmdLineOptions) -> Dict[str, T]:
    controlOptions = {}

    controlOptions["backupProperties"] = {}
    controlOptions["backupProperties"]["backupFolder"] = "/Path/to/folder/"

    controlOptions["camera"] = {}
    controlOptions["camera"]["resolution"] = {}
    controlOptions["camera"]["resolution"]["width"] = cmdLineOptions["width"]
    controlOptions["camera"]["resolution"]["height"] = cmdLineOptions["height"]
    controlOptions["camera"]["fps"] = cmdLineOptions["fps"]

    controlOptions["videoAnalyser"] = {}
    controlOptions["videoAnalyser"]["ROI"] = {}
    controlOptions["videoAnalyser"]["ROI"]["startWidth"] = 0
    controlOptions["videoAnalyser"]["ROI"]["endWidth"] = cmdLineOptions["width"]
    controlOptions["videoAnalyser"]["ROI"]["startHeight"] = 0
    controlOptions["videoAnalyser"]["ROI"]["endHeight"] = cmdLineOptions["height"]

    controlOptions["markerDetector"] = {}
    controlOptions["markerDetector"]["maxDetectionsSharedMemory"] = 20
    controlOptions["markerDetector"]["blobDetectorParams"] = {}
    controlOptions["markerDetector"]["blobDetectorParams"]["filterByArea"] = True
    controlOptions["markerDetector"]["blobDetectorParams"]["minArea"] = 300
    controlOptions["markerDetector"]["blobDetectorParams"]["maxArea"] = 1000
    controlOptions["markerDetector"]["blobDetectorParams"]["filterByCircularity"] = False
    controlOptions["markerDetector"]["blobDetectorParams"]["filterByColor"] = False
    controlOptions["markerDetector"]["blobDetectorParams"]["filterByConvexity"] = False
    controlOptions["markerDetector"]["blobDetectorParams"]["filterByInertia"] = False

    return controlOptions


def saveDemoConfigFile() -> Dict[str, T]:
    controlOptions = {}

    controlOptions["camera"] = {}
    controlOptions["camera"]["resolution"] = {}
    controlOptions["camera"]["resolution"]["width"] = 640
    controlOptions["camera"]["resolution"]["height"] = 480
    controlOptions["camera"]["fps"] = 40
    controlOptions["camera"]["exposureMode"] = "auto"
    controlOptions["camera"]["brightness"] = 50

    controlOptions["videoAnalyser"] = {}
    controlOptions["videoAnalyser"]["ROI"] = {}
    controlOptions["videoAnalyser"]["ROI"]["startWidth"] = 320
    controlOptions["videoAnalyser"]["ROI"]["endWidth"] = 640
    controlOptions["videoAnalyser"]["ROI"]["startHeight"] = 0
    controlOptions["videoAnalyser"]["ROI"]["endHeight"] = 480
    controlOptions["videoAnalyser"]["useZoom2Crop"] = False

    controlOptions["markerDetector"] = {}
    controlOptions["markerDetector"]["maxDetectionsSharedMemory"] = 20
    controlOptions["markerDetector"]["threshold"] = 50
    controlOptions["markerDetector"]["blobDetectorParams"] = {}
    # controlOptions["markerDetector"]["blobDetectorParams"]["filterByColor"] = False
    # controlOptions["markerDetector"]["blobDetectorParams"]["blobColor"] = 0
    controlOptions["markerDetector"]["blobDetectorParams"]["filterByArea"] = True
    controlOptions["markerDetector"]["blobDetectorParams"]["minArea"] = 400
    controlOptions["markerDetector"]["blobDetectorParams"]["maxArea"] = 5000
    # controlOptions["markerDetector"]["blobDetectorParams"]["filterByCircularity"] = False
    # controlOptions["markerDetector"]["blobDetectorParams"]["maxCircularity"] = 100
    # controlOptions["markerDetector"]["blobDetectorParams"]["minCircularity"] = 1000
    # controlOptions["markerDetector"]["blobDetectorParams"]["filterByConvexity"] = False
    # controlOptions["markerDetector"]["blobDetectorParams"]["maxConvexity"] = 100
    # controlOptions["markerDetector"]["blobDetectorParams"]["minConvexity"] = 1000
    # controlOptions["markerDetector"]["blobDetectorParams"]["filterByInertia"] = False
    # controlOptions["markerDetector"]["blobDetectorParams"]["maxInertiaRatio"] = 100
    # controlOptions["markerDetector"]["blobDetectorParams"]["minInertiaRatio"] = 100
    # controlOptions["markerDetector"]["blobDetectorParams"]["minDistBetweenBlobs"] = 1000

    controlOptions["dataEstimator"] = {}
    # controlOptions["dataEstimator"]["method"] = "DistanceBased"
    controlOptions["dataEstimator"]["numMarkers"] = 14
    controlOptions["dataEstimator"]["maxRPM"] = 60

    # controlOptions["dataEstimator"]["shouldSelfCalibrate"] = True # We are always self calibrating...
    controlOptions["dataEstimator"]["minNumMarkers2Calibrate"] = 3
    controlOptions["dataEstimator"]["calibrationInterval"] = 20  # Number of frames to analyse and keep calibration consistent
    controlOptions["dataEstimator"]["calibrationTimeout"] = 20  # Time for calibration to happen (in seconds),
    # after that we consider there is an issue with calibration

    controlOptions["dataEstimator"]["numFrames4Average"] = 10
    controlOptions["dataEstimator"]["backupCalibrationDist"] = 90  # This is the pixel distance between markers
    # controlOptions["dataEstimator"]["numFrames4Average_VoidFrames"] = 4
    # controlOptions["dataEstimator"]["tolerance"] = 0.15

    # controlOptions["dataEstimator"]["gaussianTolerance"] = 1.0

    controlOptions["waterMeter_GPIO"] = {}
    controlOptions["waterMeter_GPIO"]["inputPin"] = 13
    controlOptions["waterMeter_GPIO"]["intervalBetweenReads"] = 0.5
    
    controlOptions["hallSensor_GPIO"] = {}
    controlOptions["hallSensor_GPIO"]["hallPin"] = 23
    controlOptions["hallSensor_GPIO"]["intervalBetweenReads"] = 0.5
    
    controlOptions["rpmSensor_GPIO"] = {}
    controlOptions["rpmSensor_GPIO"]["rpmPin"] = 24
    controlOptions["rpmSensor_GPIO"]["intervalBetweenReads"] = 0.5

    controlOptions["bluetoothPairing"] = {}
    controlOptions["bluetoothPairing"]["timeout"] = 25  # seconds that it attempts to pair
    controlOptions["bluetoothPairing"]["GPIO_Pin"] = 17 #21
    controlOptions["bluetoothPairing"]["GPIO_Notification_Pin"] = 15 #16

    controlOptions["serverInformation"] = {}
    controlOptions["serverInformation"]["connectionTimeout"] = 5  # In seconds, Tries to grab the connection to server each n seconds
    # controlOptions["serverInformation"]["url"] = "https://web.staging.istrada.net/app/#/trucks"
    # controlOptions["serverInformation"]["mixerID"] = 1
    controlOptions["serverInformation"]["updateFrequency"] = 5  # In seconds, Frequency of communication to server. The update frequence SHOULD be divisible by sampling rate.
    # Otherwise the real update frequence will be a multiplied of the sampling rate closest to the update frequency
    controlOptions["serverInformation"]["samplingRate"] = 0.1  # In seconds, Rate at which is grabs the information from the estimator.
    controlOptions["serverInformation"]["toleranceRotation"] = 1.5  # Variations of more than toleranceRotation rpm do not count as noise. This based on the variance
    controlOptions["serverInformation"]["deviceOS"] = "Android"  # or iOS
    # controlOptions["serverInformation"]["characteristicUUID"] = 'fd758b93-0bfa-4c52-8af0-85845a74a606'
    # controlOptions["serverInformation"]["serviceUUID"] = '27cf08c1-076a-41af-becd-02ed6f6109b9'
    controlOptions["serverInformation"]["maxSamplesPerMessage"] = 10

    controlOptions["logging"] = {}
    controlOptions["logging"]["maxLogFiles"] = 20
    controlOptions["logging"]["loggingFPSFramesInterval"] = 30  # Interval at which the fps is printed (helps to control clutter)
    controlOptions["logging"]["localBackup"] = {}
    controlOptions["logging"]["localBackup"]["frequency"] = 60  # In seconds, Frequency that a file is saved to disk
    controlOptions["logging"]["localBackup"]["folder"] = "/home/AnarPi/Desktop/pi5_ble/iStradaLog"
    controlOptions["logging"]["localBackup"]["maxStoredSamples"] = 40  # Number of samples after which it will start discarding old samples

    with open('../ConfigFiles/config.yaml', 'w') as outfile:
        yaml.dump(controlOptions, outfile, default_flow_style=False)

    return controlOptions


def saveConfigFile(zoomTopLeft, zoomBotLeft, markerCropTopLeft, markerCropBotLeft, originalFilePath):
    curId = getConfigFileID(originalFilePath)

    folderPath, baseName = ntpath.split(originalFilePath)
    baseNameNoExt = baseName[:-5]

    # Load the original File
    try:
        with open(originalFilePath) as file:
            # The FullLoader parameter handles the conversion from YAML
            # scalar values to Python the dictionary format
            controlOptions = yaml.load(file, Loader=yaml.FullLoader)
    except FileNotFoundError:
        curLogger.critical("Configuration file not found. Please check the file name and path.")
        exit()

    # Update the settings
    # Get resolution
    camWidth = controlOptions["camera"]["resolution"]["width"]
    camHeight = controlOptions["camera"]["resolution"]["height"]

    controlOptions["videoAnalyser"]["ROI"]["startHeight"] = int(zoomTopLeft[0] * camHeight)
    controlOptions["videoAnalyser"]["ROI"]["startWidth"] = int(zoomTopLeft[1] * camWidth)
    controlOptions["videoAnalyser"]["ROI"]["endHeight"] = int(zoomBotLeft[0] * camHeight)
    controlOptions["videoAnalyser"]["ROI"]["endWidth"] = int(zoomBotLeft[1] * camWidth)

    controlOptions["videoAnalyser"]["ProcessingROI"]["startHeight"] = int(markerCropTopLeft[0] * camHeight)
    controlOptions["videoAnalyser"]["ProcessingROI"]["startWidth"] = int(markerCropTopLeft[1] * camWidth)
    controlOptions["videoAnalyser"]["ProcessingROI"]["endHeight"] = int(markerCropBotLeft[0] * camHeight)
    controlOptions["videoAnalyser"]["ProcessingROI"]["endWidth"] = int(markerCropBotLeft[1] * camWidth)

    controlOptions["videoAnalyser"]["useZoom2Crop"] = True

    # Define name for new file
    if curId == 0:
        newConfigFilePath = os.path.join(folderPath, baseNameNoExt + "." + str(1) + ".yaml")
    else:
        numDigits = len(str(curId))
        baseNameNoExt = baseNameNoExt[:(-1 * (numDigits + 1))]
        newConfigFilePath = os.path.join(folderPath, baseNameNoExt + "." + str(curId + 1) + ".yaml")

    # Save new file
    with open(newConfigFilePath, 'w') as outfile:
        yaml.dump(controlOptions, outfile, default_flow_style=False)

    return newConfigFilePath