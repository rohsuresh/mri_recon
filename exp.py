#import numpy as np

def readcfl(name):
    # get dims from .hdr
    h = open(name + ".hdr", "r")
    h.readline() # skip
    l = h.readline()
    h.close()
    dims = [int(i) for i in l.split()]

    # remove singleton dimensions from the end
    n = np.prod(dims)
    dims_prod = np.cumprod(dims)
    dims = dims[:np.searchsorted(dims_prod, n)+1]

    # load data and reshape into dims
    d = open(name + ".cfl", "r")
    a = np.fromfile(d, dtype=np.complex64, count=n);
    d.close()
    return a.reshape(dims, order='F') # column-major



from ismrmrd.acquisition import *

data = readcfl("/Users/rohansuresh/Downloads/t2/data")
traj = readcfl("/Users/rohansuresh/Downloads/t2/traj")

t0 = [slice(None)] * data.ndim
t0[10] = 0

data = data[t0]
traj = traj[t0]

acqh = AcquisitionHeader()
acqh.number_of_samples = np.prod(data.shape[:3])
acqh.active_channels = data.shape[3]
acqh.trajectory_dimensions = traj.shape[0]

acq = Acquisition(acqh)
acq.header = acqh

for coil in range(acqh.active_channels):
	acq.data[coil, :] = data[:, :, :, 0].flatten()

from ismrmrd.meta import *

from ismrmrd.hdf5 import *

datset = Dataset("/Users/rohansuresh/Downloads/t2/data.hdf5", "scan_0")
datset.append_acquisition(acq)

def gen_xml(dict):
        """Converts a Meta instance into a "valid" ISMRMRD Meta XML string"""
        root = ET.Element('ismrmrdHeader')
        tree = ET.ElementTree(root)
        for k, v in dict.items():
            child = ET.SubElement(root, '')
            name = ET.SubElement(child, '')
            name.text = k
            if type(v) == list:
                for item in v:
                    value = ET.SubElement(child, 'value')
                    value.text = str(item)
            else:
                value = ET.SubElement(child, 'value')
                value.text = str(v)
        # this is a 'workaround' to get ElementTree to generate the XML declaration
        output = strout()
        tree.write(output, encoding="UTF-8", xml_declaration=True)
        return output.getvalue()


sample_dict = {"number_of_samples": acqh.number_of_samples, "receiverChannels": acqh.active_channels, "trajectory_dimensions": acqh.trajectory_dimensions, "H1resonanceFrequency_Hz": 63500000, "matrixSize": [{"x": 512}, {"y": 256}, {"z": 1}], "fieldOfView": [{"x": 600}, {"y": 300}, {"z": 6}], "Trajectory": "Cartesian", "encodingLimits": [{"minimum": 0}, {"maximum": 255}, {"center": 128}] }
meta = Meta(sample_dict)
xml_string = gen_xml(meta)

write = datset.write_xml_header(xml_string)
read = datset.read_xml_header()
depth = datset._dataset


datset.header = xml_string

datset.close()

