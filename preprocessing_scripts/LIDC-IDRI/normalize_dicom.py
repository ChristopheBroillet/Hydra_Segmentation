import numpy as np
from PIL import Image
import pydicom


def get_LUT_value(numpyArray, windowWidth, windowCenter, rescaleSlope, rescaleIntercept):
    """Apply the RGB Look-Up Table for the given data and window/level value.
    @params:
        numpyArray - Required: NumPy array containing the value of each pixel, 16 bits per pixel
        windowWidth- Required: dataset.WindowWidth (cannot appear without WindowCenter)
        windowCenter - Required: dataset.WindowCenter (cannot appear without WindowWidth)
        rescaleSlope - Required: specify the linear transformation from pixels in their stored on disk representation to their
                       in memory representation
        rescaleIntercept - Required: specify the linear transformation from pixels in their stored on disk representation to their
                       in memory representation
    """

    # Hounsfield unit:
    # Hounsfield Units (HU) are used in CT images it is a measure of radio-density, calibrated to distilled water and free air.
    # HUs can be calculated from the pixel data using the Slope and Intercept value from the Dicom image
    # and applying it to a target pixel.
    # HU = m * P + b
    # Where: m is the Dicom attribute (0028,1053) “Rescale slope”
    #        b is the Dicom attribute (0028,1052) “Rescale intercept”
    #        P is the value of that particular pixel in the pixels array.
    # https://www.medicalconnections.co.uk/kb/Hounsfield-Units/

    if rescaleSlope != None and rescaleIntercept != None:
        numpyArray = numpyArray * rescaleSlope + rescaleIntercept

    if isinstance(windowCenter, pydicom.multival.MultiValue):
        windowCenter = windowCenter[0]

    if isinstance(windowWidth, pydicom.multival.MultiValue):
        windowWidth = windowWidth[0]

    # np.piecewise iterates through an array, checks the given conditions on each element, returns the corresponding value of the last array
    # Example:
    ### x = np.array([1,2,3,4])
    ### np.piecewise(x, [x < 3, x >= 3], [0,1])
    ### --> array([0, 0, 1, 1])
    # http://dicom.nema.org/medical/dicom/2014a/output/pdf/part03.pdf page 1057
    numpyArray = np.piecewise(numpyArray,
    [numpyArray<= windowCenter-0.5-(windowWidth-1)/2, numpyArray>windowCenter - 0.5 + (windowWidth-1) /2],
    [0, 255, lambda x: ((x - (windowCenter - 0.5)) / (windowWidth-1) + 0.5) * (255 - 0) + 0 ])

    return numpyArray.astype('uint8')

    # BEFORE:
    # conversion 16 bits to 8 bits array: [0:MAXARRAY] -> [0:255]
    # ratio = np.max(numpyArray) / 255 ;
    # return (numpyArray/ ratio).astype('uint8')




def get_normalized_array(dataset, flip=False):
    """Get normalized NumPy array from DICOM file
    @params:
        dataset   - Required : FileDataset (Pydicom) corresponding to one specific slice
    """
    # dataset without pixels
    if ('PixelData' not in dataset):
        raise TypeError("DICOM dataset does not have pixel data")

    # WindowWidth and WindowCenter are available in dataset
    if ('WindowWidth' in dataset) and ('WindowCenter' in dataset):
        if ('RescaleSlope' in dataset) and ('WindowCenter' in dataset):
            image_array = get_LUT_value(dataset.pixel_array, dataset.WindowWidth, dataset.WindowCenter,
            dataset.RescaleSlope, dataset.RescaleIntercept)
        else:
            image_array = get_LUT_value(dataset.pixel_array, dataset.WindowWidth, dataset.WindowCenter,
            None, None)

        if flip:
            image_array = 255 - image

        # return the normalized pixel values
        return image_array

    # dataset without windowWidth/WindowCenter -> unable to compute the linear transformation
    else:
        # number of bits allocated for each pixel (each sample/channel should have the same number of bits allocated)
        # either 1 or a multiple of 8
        bits = dataset.BitsAllocated

        # number of "channels" (RGB = 3, greyscale = 1 etc.) / number of separates planes in the image
        # either 1 or 3 planes
        samples = dataset.SamplesPerPixel

        # Get raw pixel values of the DICOM
        ds = dataset.pixel_array

        # 1 bit per pixel, 1 plane
        if bits == 1 and samples == 1:
            if flip:
                ds = 1 - ds

        # 1 plane = greyscale
        elif bits == 8 and samples == 1:
            if flip:
                ds = 255 - ds

        # 3 planes = RBG
        elif bits == 8 and samples == 3:
            if flip:
                ds = 255 - ds

        elif bits == 16:
            ds = (ds.astype(np.float)-ds.min())*255.0 / (ds.max()-ds.min())

            if flip:
                ds = 255 - ds

            ds = ds.astype(np.uint8)

        else:
            raise TypeError("Don't know PIL mode for %d BitsAllocated and %d SamplesPerPixel" % (bits, samples))

        # return the normalized pixel values
        return ds




def get_PIL_image(dataset, flip=False):
    """Get Image object from Python Imaging Library(PIL)
    @params:
        dataset   - Required : FileDataset (Pydicom) corresponding to one specific slice
    """
    # dataset without pixels
    if ('PixelData' not in dataset):
        raise TypeError("Cannot show image -- DICOM dataset does not have pixel data can only apply LUT if these window info exists")


    # WindowWidth and WindowCenter are available in dataset
    if ('WindowWidth' in dataset) and ('WindowCenter' in dataset):
        if ('RescaleSlope' in dataset) and ('RescaleIntercept' in dataset):
            image = get_LUT_value(dataset.pixel_array, dataset.WindowWidth, dataset.WindowCenter,
            dataset.RescaleSlope,dataset.RescaleIntercept)
        else:
            image = get_LUT_value(dataset.pixel_array, dataset.WindowWidth, dataset.WindowCenter,
            None, None)

        if flip:
            image = 255 - image

        # return a PIL.Image of 8 bits per pixel greyscale, L mode
        return Image.fromarray(image)


    # dataset without windowWidth/WindowCenter -> unable to compute the linear transformation
    else:
        # number of bits allocated for each pixel (each sample/channel should have the same number of bits allocated)
        # either 1 or a multiple of 8
        bits = dataset.BitsAllocated

        # number of "channels" (RGB = 3, greyscale = 1 etc.) / number of separates planes in the image
        # either 1 or 3 planes
        samples = dataset.SamplesPerPixel

        # Get raw pixel values of the DICOM
        ds = dataset.pixel_array

        # 1 bit per pixel, 1 plane (Not tested yet)
        if bits == 1 and samples == 1:
            mode = '1'

            if flip:
                ds = 1 - ds

        # 1 plane = greyscale
        elif bits == 8 and samples == 1:
            mode = "L"

            if flip:
                ds = 255 - ds

        # 3 planes = RBG
        elif bits == 8 and samples == 3:
            mode = "RGB"

            if flip:
                ds = 255 - ds

        elif bits == 16:
            mode = "I"
            norm = (ds.astype(np.float)-ds.min())*255.0 / (ds.max()-ds.min())

            if flip:
                norm = 255 - norm

            norm = Image.fromarray(norm.astype(np.uint8)).convert('L')
            return norm

        else:
            raise TypeError("Don't know PIL mode for %d BitsAllocated and %d SamplesPerPixel" % (bits, samples))

        # PIL size = (width, height)
        size = (dataset.Columns, dataset.Rows)

        # create an image memory referencing pixel data in a byte buffer
        return Image.frombuffer(mode, size, ds, "raw", mode, 0, 1)




def save_PIL(dataset):
    """Display an image using the Python Imaging Library (PIL)"""
    im = get_PIL_image(dataset)
    return im
