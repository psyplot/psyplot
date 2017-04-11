from psyplot.config.rcsetup import RcParams, validate_dict


plugin_version = '1.0.0'


rcParams = RcParams(defaultParams={
    'test': [1, lambda i: int(i)],
    'project.plotters': [
        {'test_plotter': {
            'module': 'psyplot_test.plotter',
            'plotter_name': 'TestPlotter', 'import_plotter': True}},
        validate_dict]})
rcParams.update_from_defaultParams()


patch_check = []

checking_patch = False


def test_patch(plotter_d, versions):
    if not checking_patch:
        raise ValueError("Accidently applied the patch!")
    patch_check.append({'plotter': plotter_d, 'versions': versions})


patches = {('psyplot_test.plotter', 'TestPlotter'): test_patch}
