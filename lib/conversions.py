

from nc_library import loop_mirror_terminator, mmi1x2, lys
from phidl import geometry as pg, Device
import meep as mp

silicon = mp.Medium(epsilon=12)
cell_material = {}
port_source = {}


def get_layer_mapping(layerset):
    return {
        layerset['wg_deep'].gds_layer: silicon,
        layerset['FLOORPLAN'].gds_layer: cell_material,
        1: port_source,
        2: port_source,
    }


def device_to_meep(device, mapping):
    # converts PHIDL to MEEP. You must give a layer mapping that can be derived from get_layer_mapping
    # TODO: partial etches. Currently this is only 2D
    geometry = []
    for poly_grp in device.polygons:
        layer = poly_grp.layers[0]
        try:
            material = mapping[layer]
        except KeyError:
            print(f'layer {layer} not in meep mapping')
            continue
        if material is cell_material:
            cell = mp.Vector3(poly_grp.xsize, poly_grp.ysize)
            continue
        elif material is port_source:
            continue
        for poly in poly_grp.polygons:
            vertex_list = [mp.Vector3(vertex[0], vertex[1]) for vertex in poly]
            geometry.append(mp.Prism(vertex_list, height=0, material=material))
    return cell, geometry


def gds_to_meep(filename):
    D = Device('gdsext')
    D.load_gds(filename)
    D.flatten()
    return device_to_meep(D)


def give_loopmirror(gap=.5):
    # just an example of augmenting a normal phidl device (loop_mirror_terminator)
    # giving it as a phidl Device as well as port, bounding box, and source things used by MEEP
    D = Device('loopmirror')

    cell = D << pg.rectangle([31, 15], layer=lys['FLOORPLAN'])
    cell.center = (0, 0)

    access = D << pg.compass([8, .35], layer=lys['wg_deep'])
    access.y = cell.y
    access.xmin = cell.xmin

    mmi = mmi1x2(gap_mmi=.5)
    loop = D << loop_mirror_terminator(y_splitter=mmi)
    loop.connect('wg_in_1', access.ports['E'])

    medium_map = get_layer_mapping(lys)

    port = D << pg.rectangle([.1, 1], layer=1)
    source = D << pg.rectangle([.1, 1], layer=2)
    port.y = 0
    source.y = 0
    port.x = loop.xmin - 6
    source.x = loop.xmin - 7

    D.flatten()
    return D

