# Example: Imports (Guidelines §5)

## BAD
Mixed order — standard library, local, and third-party imports interleaved
with no grouping or alphabetization.

```python
import json
from app.models import Order
import os
from app.db import get_connection
import requests
```

## GOOD
Standard library, then third-party, then local — each group blank-line
separated and alphabetized within the group.

```python
import json
import os

import requests

from app.db import get_connection
from app.models import Order
```

**Why:** Consistent import ordering makes it immediately obvious which
dependencies are stdlib, external packages, vs. internal modules — useful
when auditing what a file actually depends on, and it eliminates noisy diffs
from imports being reordered inconsistently across commits.
