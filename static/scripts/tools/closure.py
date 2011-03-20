import os
import tempfile

tempdir = tempfile.gettempdir()

path = os.path.abspath(os.path.join(os.path.dirname(__file__), "compiler.jar"))
if not os.path.exists(path):
    raise Exception("No closure compiler.jar at %s; read README.txt!" % path)

def minimize(code):
    # Cannot keep these files open on Windows since file cannot then be read by Java
    ntf = tempfile.NamedTemporaryFile(delete=False)
    ntf.write(code)
    ntf.flush()
    ntf.close()

    ntf2 = tempfile.NamedTemporaryFile(delete=False)
    ntf2.close()

    os.system("java -jar %s --js %s --js_output_file %s" % (path, ntf.name, ntf2.name))
    ntf2 = file(ntf2.name, "r")
    data = ntf2.read()
    ntf2.close()
    os.unlink(ntf2.name)
    os.unlink(ntf.name)
    return data
