from tesla.spatial.subr import regioncfg
from tesla.servlet.tps.metadata.common import DATA_UNIFIED_TYPES, ALL_LAYERS
from tesla.spatial.mobius import session
from tesla.spatial.mobius.nbm_interface import UnifiedGenerations

def getId():
    region = "USA"
    genPath = regioncfg.get_map_path(region)
    unified_gen = UnifiedGenerations(genPath)
    layer_number = unified_gen.layer_number

    generation = {}
    for layers in ALL_LAYERS:
        if layers.startswith('MAT'):
            for keys in ['NMAT', 'DMAT']:
                gen = unified_gen.get_generation(layer_number[keys])
                generation[keys] = str(gen)
        elif layers.startswith('BR'):
            gen = unified_gen.get_generation(layer_number['BR'])
            generation[layers] = str(gen)
        elif layers.startswith('LBL'):
            gen = unified_gen.get_generation(layer_number['LBL'])
            generation[layers] = str(gen)
        elif layers in layer_number:
            gen = unified_gen.get_generation(layer_number[layers])
            generation[layers] = str(gen)
    return generation


if __name__ == "__main__":
    generation = getId()
    layersInOrder = [k for k in generation.iterkeys()]
    layersInOrder.sort()
    for k in layersInOrder:
        print "%s:\t%s" % (k, generation[k])


