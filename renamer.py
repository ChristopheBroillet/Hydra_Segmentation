import pydicom
from pydicom.data import get_testdata_file
import os


path_to_dataset = "/home/christophe/Desktop/DataSet" # absolute path

# print(os.path.join(path_to_dataset, "test"))

patients_list = os.listdir(path_to_dataset)
assert patients_list
# iterate over all patients
for patient in patients_list:
    patient_path = os.path.join(path_to_dataset, patient)
    studies_list = os.listdir(patient_path)
    assert studies_list
    # iterate over all dates
    for study in studies_list:
        study_path = os.path.join(patient_path, study)
        series_list = os.listdir(study_path)
        assert series_list
        # iterate over all series
        for serie in series_list:
            # list all dicom files in the current serie
            serie_path = os.path.join(study_path, serie)
            dicom_names_list = os.listdir(serie_path)
            assert dicom_names_list
            dicom_path = os.path.join(serie_path, dicom_names_list[0])
            # open a dicom file in the current serie
            ds = pydicom.dcmread(dicom_path)
            # replace '/' by '_' to avoid conflict
            new_name = ds.SeriesDescription.replace('/', '_')
            # renaming the folder serie
            os.rename(serie_path, os.path.join(study_path, new_name))

# look at class "path"
# search for §compose key§
# jupyter notebook (Ipython) and play with pydicom to see what it can do
# go through the notes and learn as much as possible
# search for dicom viewer ubuntu on google