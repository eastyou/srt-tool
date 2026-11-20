"""支持 ``python -m srttool`` 运行。"""

import sys

from srttool.cli import main

if __name__ == "__main__":
    sys.exit(main())
