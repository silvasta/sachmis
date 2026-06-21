Ok lets handle this first, I need just a brief answer on the NOTE:

```py
class DagOperator:
    """Quite sure I will violate the strict bDAG rules somewhen...
    or even move to something else, so this is like a trap?"""

class GraphOperator:
    """This sound even as it could be an operator for graphics,
    or work with more flexible graphs..."""

class SproutOperator:
    """
    Extract DAG from active Tree and support running Models with Data IO

    # NOTE: now I am sure, this is the final decision!

    Extract DAG from active Tree and support running Agents with Data IO
    """

```

---

я подготовил финальный коде ожидание.

Анализирую структуру и дайте советы

---

This time I worked from the bottom upwards (sstcore library, utils, config, data, now...), before I finish the final transformation of data I will go trough the core to avoid some fails again for preparing a pipeline that just works for 95% of the cases.

So far the core or the agents/models were usually the easy thing, except when I changed some boundaries, but then it was usually a quick re-setup. Now a deep refactor was needed to improve the capabilities of the pipeline and I think the Agents will be ready very fast, soon with structured responses and more features.

One challenge now is to design the sprout such that it goes on tour with the data package, ok that worked before, except for multi turns, they failed for the new Arboreal and never worked for Gemini... Anyway, before data I refactored the CLI engine heavily and created a lot of Exceptions and Handlers, I hope they will expose the bugs now.

The major challenge is to think again about the launch of capstone.Fire including the ForestExtractor and MarkdownIO, the TreeExtractor will maybe be delayed before or after the selection, but most likely outside session.**enter**.

Another important task is to decide about Contexts and Exitstack. The small issue is to find a proper package and module for the Extractors. More challenging is to decide where to open, attach and close which context.

Current Idea:

- open session
- open data, attach it to session and maybe to stack, let data open MarkdownOperator (probably after init) MO will the scan the folder with exit on fail
- setup CampOperator
- open forest, attach forest registries to camp, NEW: attach forest context to data (I will now let data handle the the ArboErrors first)
- tree extract will most likely be moved out of session.**enter**

End of opening session context

- NEW: tree will be opened here to confirm MO scan and that tree can be opened and closed, no write now just extract the dag (for previous conversations)
- then I prepare model args with launch of TUI selector
- load files, images role, inside camp (if some) and some other selections, Uploader is called if needed

Quick info: this pipeline is designed to reduce loss of user effort for early terminations therefore critical operations are planned at early and time consuming operations like TUI select are planed later, with model select and agent boot in the middle.

- Now I display everything, the most important infos at the bottom for best visibility and let it confirm
- Lauch models (or agents) let them extract the raw response from their provider (every extraction that is related to their specific SDK), then they use the sprout as connection for sending the response parts home to the SproutOperator.
- NEW:
  - SO assembles response parts to final BaseModel-Response, ready for write and attach to DAG

NOTE: maybe assemble the Prompt here as well, before it was done earlier but maybe that is not needed, that required to lock and write the tree earlier just for a new local_id... local_id: fragile feature of the current status, important feature for user experience, perfectly grouped files and easy selection of sprouts, just type an increasing int. But I need to ensure that the pipeline doesn't depend on parsing this local_id backwards from names of files written to a user folder, even if I am the user...

- Then first write the Markdown response to `r_i_model_topic.md`
- Rotate `prompt.md` to `p_i_topic.md` into same folder as response (only on first return)
- NEW: for multiple responses I am thinking about opening the tree after every API call and attach response by response, otherwise I will attach the entire conversation to the internal growing dag and finally commit that as 1 piece with the new loaded prompt as head.

NOTE: for the graph it doesn't even matter when, where or what attaches. The attach will always be a leave or subtree, and any valid attach is just a new member in a list of successors of a response.
When other processes attach in between there should be no issue (can happen, is the reason for this multi load locked json setup...)

- Finally: someone will print the result file paths that MO has written, relative to cwd and as: `nvim path1.. pathN` such that i can directly render it from there flat and static in FireFox, extract code in the editor and prepare the next session.

That is the screenplay for `capstone.Fire` that operates turn by turn. Later I will implement `capstone.Thunder` hopefully far before the exam period starts. I assume it to be easier as I will work with always locked and multiple trees but without any IO parsing and less writing.

It worked quite good in February but needed so much effort for debug and manual gluing everything together... as soon as the pipeline worked it provided amazing results but the maximal complexity was limited.

Now I will finish the more advanced pipeline that provides as well much more comfort. Then the refactoring of the exam material will be a piece of cake, after thousands of hours... At the beginning I actually thought that I will save time with this idea... but it was way more interesting and fun than university stuff and I already learnt more about Python and programming in 1 year as I knew that it exits.

## Code Base

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/model/__init__.py
"""
Model for Execution - The Purpose of the entire Pipeline

The Base and the Controller of the Execution is in 'agent'

Gemini and Grok provide custom adapters for their APIs

'launch' is the collector for a general pipeline interface

"""

__all__: list[str] = [
    "Model",
    "Grok",
    "Gemini",
    "launch",
]
from . import launch
from .agent import Model
from .gemini import Gemini
from .grok import Grok

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/model/agent.py
from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from ...config.defaults import ModelParam
from ...config.models import ModelFamily
from ...data.conversation import Prompt
from ...utils.print import printer
from ..sprout import Sprout


class Model(ABC):
    """Framework + every execution will be done from method here"""

    _raw_response: Any | None = None

    def __init__(self, sprout: Sprout, param: ModelParam | None = None):
        logger.debug(f"Loading {sprout.model.api_name}")

        self.sprout: Sprout = sprout
        self.param: ModelParam = self._load_param(param)

        logger.debug(f"Model ({self.__class__.__name__}) connected with Data")

        self._load_client()
        self._prepare_chat()

        logger.info(f"Model loaded: {self.__class__.__name__}")

    @property
    def model(self) -> ModelFamily:
        return self.sprout.model

    @property
    def has_previous_id(self) -> bool:
        """Look at Sprout and find previous Response ID"""
        return self.sprout.previous_remote_id is not None

    @property
    def prompt(self) -> Prompt:
        """Look at Sprout and find previous Response ID"""
        return self.sprout.prompt

    @abstractmethod
    def _load_param(self, param: ModelParam | None) -> ModelParam:
        """Load defaults if param not set"""

    @abstractmethod
    def _load_client(self, *args, **kwargs):
        """Complete authentication and create Client object"""

    @abstractmethod
    def _prepare_chat(self, *args, **kwargs):
        """Load chat with params defined per Model"""

    def assemble_prompt(self):
        logger.info("Start assembling prompt")
        self.attach_role()
        logger.debug("role attached")
        self._attach_prompt(prompt=self.sprout.prompt.content)
        logger.debug("prompt attached")
        self._attach_images()
        logger.debug("images attached")
        self._attach_files()
        logger.debug("files attached")

    def attach_role(self):
        if role := self.sprout.prompt.role:
            self._attach_role(role.content)
            logger.debug(f"using role: {role.name}")
        else:
            logger.debug("using no role")

    @abstractmethod
    def _attach_role(self, role: str):
        pass

    @abstractmethod
    def _attach_prompt(self, prompt: str):
        pass

    @abstractmethod
    def _attach_images(self):
        pass

    @abstractmethod
    def _attach_files(self):
        pass

    def fire(self):
        """Release prompt and process response"""
        logger.info("Fire")

        self.get_response()
        logger.info("Got response, start processing...")

        self.process_response()

    def get_response(self):
        printer.special(f"Start of Call: {self}")
        self._raw_response: Any = self._get_response()

    @abstractmethod
    def _get_response(self):
        pass

    def process_response(self):
        # raise
        full_response: str = self._extract_full_response()
        self.sprout.collect_raw_response(full_response)

        # maybe raise
        response_id: str = self._extract_response_id()
        content: str = self._extract_response_content()

        printer.success(f"Response Content ({self.model.cli})")
        printer.success(f"Response Content ({self.model.id_cli})")
        printer.md(content)

        # no raise
        usage: dict = self._extract_usage() or {}

        if not self._calculate_usage_cost(usage):
            # Print raw usage, _calculate_usage prints when not failed
            printer(usage)

        self.sprout.collect_response_data(
            content=content,
            remote_id=response_id,
            usage=usage,
        )
        logger.info(f"Response Forwarded: {self.model.unique}")

    @abstractmethod
    def _extract_full_response(self) -> str:
        pass

    @abstractmethod
    def _extract_response_content(self) -> str:
        pass

    @abstractmethod
    def _extract_response_id(self) -> str:
        pass

    @abstractmethod
    def _extract_usage(self) -> dict | None:
        pass

    @abstractmethod
    def _calculate_usage_cost(self, usage) -> bool:
        # TODO: ensure this prints calculate usage
        pass

    # LATER: new methods, e.g.
    # - image receive
    # - chains
    # - MCP

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/model/gemini.py
from google.genai import Client, types
from google.genai.types import GenerateContentResponse
from loguru import logger

from ...config import config
from ...config.defaults import GeminiParam, ModelParam
from ...config.models import Geminis
from ...data.files import GoogleUploadState
from ...exceptions import SachmisDataError
from ...utils.print import printer
from .agent import Model


class Gemini(Model):
    model: Geminis
    param: GeminiParam
    client: Client
    _raw_response: GenerateContentResponse

    def _load_param(self, param: ModelParam | None) -> GeminiParam:
        """Load defaults if param not set"""
        # LATER: centralize
        if param is None:
            param: GeminiParam = config().defaults.gemini
        if isinstance(param, GeminiParam):
            return param
        # LATER: imprve
        raise SachmisDataError(f"{self.__class__.__name__}: Invalid {param=}")

    def _load_client(self):
        self.client = Client(
            api_key=config().from_env(key="GEMINI_API_KEY"),
        )

    def _prepare_chat(self):
        self.contents: list = []  # INFO: this is where all files,images, role and prompt get collected
        self.content_config: dict = {}
        if self.param.thinking_budget:
            self.content_config |= {
                "thinking_config": types.ThinkingConfig(
                    thinking_budget=self.param.thinking_budget
                ),
            }
        if self.has_previous_id:
            logger.info(  # TASK: Gemini Previous
                "Answer to Gemini here but, prepare file structure first!"
            )

    def _attach_role(self, role: str):
        self.content_config |= {"system_instruction": role}

    def _attach_prompt(self, prompt: str):
        self.contents.append(prompt)

    def _attach_images(self):
        for i in self.prompt.images:
            # FIX: image
            # mime: str = (
            #     "image/png" if i.startswith(b"\x89PNG") else "image/jpeg"
            # )
            # self.contents.append(
            #     types.Part.from_bytes(data=i, mime_type=mime),
            # )
            # TODO: images loading
            # def load_input_image(self, image_path: Path) -> None:
            #     """So far, encoding image to base64 string"""
            #
            #     # bytes image loading for gemini
            #     if image := load_bytes_image(image_path):
            #         self.bytes_images.append(image)
            #     else:
            #         logger.warning(f"Bytes image loading failed: {image_path}")
            #     self.input_image_paths.append(image_path)
            logger.debug(f"ignoring {i}")

    def _attach_files(self):
        for upload_file in self.prompt.files:
            state = upload_file.get_remote_state(self.model.target)
            if isinstance(state, GoogleUploadState):
                self.contents.append(
                    types.Part.from_uri(
                        file_uri=state.g_uri,
                        mime_type=state.g_mime_type,
                    )
                )
                logger.debug(f"loaded: {upload_file.name=}, {state.g_uri}")
            else:
                logger.warning(f"Failed: {upload_file=}")

    def _get_response(self):
        response: GenerateContentResponse = (
            self.client.models.generate_content(
                model=self.model.api_name,
                contents=self.contents,
                config=types.GenerateContentConfig(**self.content_config),
            )
        )
        return response

    def _extract_full_response(self) -> str:
        try:
            return str(self._raw_response)
        except Exception as e:
            logger.error(f"Error for response: {self.model.api_name}\n{e}")
            raise

    def _extract_response_content(self) -> str:
        try:
            return self._raw_response.text or ""
        except Exception as e:
            logger.error(f"Error for content: {self.model.api_name}\n{e}")
            raise

    def _extract_response_id(self) -> str:
        try:
            return self._raw_response.response_id or "FAIL"
        except Exception as e:
            logger.error(f"Error for ID: {self.model.api_name}\n{e}")
            return "FAIL"

    def _extract_usage(self) -> dict | None:
        try:
            if self._raw_response.usage_metadata is None:
                logger.error(f"Fail with usage_metadata! {self.model=}")
            else:
                return self._raw_response.usage_metadata.model_dump()
        except Exception as e:
            logger.error(f"Usage {self.model.unique}:\n{e}")

    def _calculate_usage_cost(self, usage: dict) -> bool:
        printer("NotImplemented! Usage calculation for Gemini")
        _usage = usage
        return False

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/model/grok.py
from google.protobuf import json_format
from loguru import logger
from xai_sdk import Client
from xai_sdk.chat import Response, file, image, system, user
from xai_sdk.sync.chat import Chat

from ...config import config
from ...config.defaults import GrokParam, ModelParam
from ...config.models import Groks
from ...data.files import XaiUploadState
from ...exceptions import SachmisDataError
from .agent import Model


class Grok(Model):
    model: Groks
    param: GrokParam
    client: Client
    chat: Chat
    _raw_response: Response

    def _load_param(self, param: ModelParam | None) -> GrokParam:
        """Load defaults if param not set"""
        # LATER: centralize
        if param is None:
            param: GrokParam = config().defaults.grok
        if isinstance(param, GrokParam):
            return param
        # LATER: imprve
        raise SachmisDataError(f"{self.__class__.__name__}: Invalid {param=}")

    def _load_client(self):
        self.client = Client(
            api_key=config().from_env(key="XAI_API_KEY"),
            timeout=self.param.timeout,
        )

    def _prepare_chat(self):
        param: dict = {
            "model": self.model.api_name,
            "store_messages": self.param.store_messages,
        }
        if id := self.sprout.previous_remote_id:
            logger.debug("got locator")
            param |= {"previous_response_id": id}
            logger.info(f"{self.model} attaches previous response with: {id=}")

        if self.model == Groks.G420M:
            param |= {"agent_count": self.param.n_agents}

        logger.debug(f"{param=}")
        self.chat: Chat = self.client.chat.create(**param)

    def _attach_role(self, role: str):
        self.chat.append(system(role))

    def _attach_prompt(self, prompt: str):
        self.chat.append(user(prompt))

    def _attach_images(self):
        # TASK: check image input again, base64 still needed?
        # - create structure to collect used images
        # - input images/FILES from file/pick/list/folder?
        for i in self.prompt.images:
            # FIX: apply base64 transform
            self.chat.append(
                user(image(image_url=f"data:image/jpeg;base64,{i}"))
                # LATER: jpeg? worked with png but clarify somewhen
            )

    # def load_input_image(self, image_path: Path) -> None:
    #     """So far, encoding image to base64 string"""
    #
    #     # b64 string images loading for grok
    #     if image := load_b64_and_encode(image_path):
    #         self.base64_images.append(image)
    #     else:
    #         logger.warning(f"Base 64 image loading failed: {image_path}")

    def _attach_files(self):
        for upload_file in self.prompt.files:
            state = upload_file.get_remote_state(self.model.target)
            if isinstance(state, XaiUploadState):
                self.chat.append(user(file(state.x_id)))
                logger.debug(f"loaded: {upload_file.name=}, {state.x_id}")
            else:
                logger.warning(f"Failed: {upload_file=}")

    def _get_response(self):
        response: Response = self.chat.sample()
        return response

    def _extract_full_response(self) -> str:
        try:
            return str(self._raw_response)
        except Exception as e:
            logger.error(f"Error for response: {self.model.api_name}\n{e}")
            raise

    def _extract_response_content(self) -> str:
        try:
            return self._raw_response.content
        except Exception as e:
            logger.error(f"Error for content: {self.model.api_name}\n{e}")
            raise

    def _extract_response_id(self) -> str:
        try:
            return self._raw_response.id
        except Exception as e:
            logger.error(f"Error for ID: {self.model.api_name}\n{e}")
            return "FAIL"

    def _extract_usage(self) -> dict | None:
        try:
            return json_format.MessageToDict(self._raw_response.usage)
        except Exception as e:
            logger.error(f"Usage {self.model.unique}:\n{e}")
            return None

    def _calculate_usage_cost(self, usage: dict) -> bool:
        try:
            # TODO: ensure this prints calculate usage
            self.model.usage_cost(token_usage=usage)
            return True
        except Exception as e:
            logger.error(f"Usage calculation {self.model.unique}: {e}")
            return False

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/model/launch.py
import time
from collections.abc import Callable

from loguru import logger

from ...utils import printer
from .agent import Model


def models(agents: list[Model], use_async=False, dry_run=False):
    """Dispatch and launch Models by Pipeline"""

    launch_methods: dict[tuple[bool, bool], Callable] = {
        (False, False): sequential_pipeline,
        (False, True): async_pipeline,
        (True, False): dry_run_sequential_pipeline,
        (True, True): dry_run_async_pipeline,
    }
    launch_methods[(dry_run, use_async)](agents)


def sequential_pipeline(models: list[Model]):
    """Launch Sequential Pipeline"""

    logger.info("Start of sequential pipeline")

    from tqdm import tqdm

    for model in tqdm(models):
        try:
            model.assemble_prompt()
            model.fire()
        except Exception as e:
            logger.error(
                f"Problem with {model}:"
                f"{model.model.unique} caused {type(e)}, details:\n{e}"
            )


def dry_run_sequential_pipeline(models: list[Model]):
    """Launch dry-run for sequential pipeline"""

    logger.info("DRYRUN - Start of sequential pipeline")

    from tqdm import tqdm

    for model in tqdm(models):
        printer(model.model.api_name)
        model.assemble_prompt()
        time.sleep(1)


def async_pipeline(models: list[Model]):
    """Launch Async Pipeline"""

    logger.info("Start of async pipeline")

    import asyncio

    from tqdm.asyncio import tqdm

    async def pipeline(models: list[Model]):
        printer.title(f"Launching Thunder with {len(models)} models")
        tasks: list = [model.fire() for model in models]
        results = await tqdm.gather(*tasks, return_exceptions=True)
        for model, result in zip(models, results, strict=False):
            model.assemble_prompt()  # WARN: model.assemble_prompt() needed, proper here?
            if isinstance(result, Exception):
                logger.error(
                    f"Problem with model {model.model.unique}: {result}"
                )
            else:
                logger.success(f"Model {model.model.unique} successful")

    asyncio.run(pipeline(models))


def dry_run_async_pipeline(models: list[Model]):
    """Launch dry-run for async pipeline"""

    logger.info("DRYRUN - Start of async pipeline")

    import asyncio

    from tqdm.asyncio import tqdm

    async def pipeline(models: list[Model]):
        printer.title(f"Launching {len(models)} models")
        for model in tqdm(models):
            printer(model.model.api_name)
            model.assemble_prompt()
            await asyncio.sleep(1)

    asyncio.run(pipeline(models))

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/retry/__init__.py
from .base import base_model, push_forward, relaxed, rich_style

# TASK: proper tenacity setup

__all__: list[str] = [
    "base_model",
    "rich_style",
    "relaxed",
    "push_forward",
]

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/context/__init__.py
"""
Provide long term window for safe data management

- ForestExtractor: Open Forest, close it, ensure data back transport
- TreeExtractor: Open Tree, close it, ensure data back transport

"""

__all__: list[str] = [
    "ForestExtractor",
    "TreeExtractor",
]
from .extract_forest import ForestExtractor
from .extract_tree import TreeExtractor

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/context/extract_forest.py
from contextlib import AbstractContextManager

from loguru import logger

from ...config import config
from ...data import DataManager
from ...data.arboreal import ArborealTracker, Forest, Tree


class ForestExtractor(AbstractContextManager):
    """Ensure Forest Data is loaded at start and saved at exit"""

    def __init__(self, data: DataManager):

        logger.debug("Loading Forest...")
        self.data: DataManager = data

        with Forest.edit_mode(path := config().paths.forest_file) as forest:
            self.tracker: ArborealTracker[Forest] = forest.sample_tracker(path)

            tree_tracker: ArborealTracker[Tree] = (
                forest.provide_tree(tree_id)
                if (tree_id := data.front.scanned_tree_id)
                else forest.attach_new_tree(data.front.topic)
            )
            data.attach_handler(tree_tracker)
            data.attach_camp(forest.get_camp())

        logger.debug("Forest Data extracted - Closing Forest for now...")

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        logger.debug("...Forest Extractor 󱢗")

        if exc_type is not None:  # LATER: what can happen?
            logger.warning(f"Task failed with {exc_type.__name__}")
            return config().defaults.context.forest_error.swallow

        logger.debug("Loading Forest...")
        with Forest.edit_mode(self.tracker.path) as forest:
            forest.attach_camp_back_by_mirror(self.data.camp)
            # LATER: confirm Tree(id), maybe after first response written?

        logger.debug("Forest closed - Data transferred back")
        return config().defaults.context.forest_end.swallow

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/context/extract_tree.py
from contextlib import AbstractContextManager

from loguru import logger

from sachmis.utils import printer

from ...config import config
from ...data import DataManager
from ...data.arboreal import ArborealTracker, Tree


class TreeExtractor(AbstractContextManager):
    """Ensure Tree Data is loaded at start and saved at exit"""

    def __init__(self, data: DataManager):

        # LATER: check moving load after selection

        logger.debug("Loading Tree...")
        self.data: DataManager = data

        with Tree.edit_mode(path := data.handler.tree_tracker.path) as tree:
            self.tracker: ArborealTracker[Tree] = tree.sample_tracker(
                path, local_id=data.handler.tree_tracker.local_id
            )
            self.data.extract_from_tree(tree)

        logger.debug("Tree Data extracted - Closing Tree for now...")

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        logger.debug("...Tree Extractor ")

        if exc_type is not None:  # LATER: what can happen?
            logger.warning(f"Task failed with {exc_type.__name__}")
            return config().defaults.context.tree_error.swallow

        logger.debug("Loading Tree...")
        with Tree.edit_mode(self.tracker.path) as tree:
            self.data.handler.attach_data_back(tree)
            printer.title("Tree")
            printer(tree.dag)

        logger.debug("Tree closed - Data transferred back")
        return config().defaults.context.tree_end.swallow

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/capstone.py
from collections import deque
from contextlib import AbstractContextManager, ExitStack
from typing import Self

from loguru import logger

from ..config.defaults import ModelParam
from ..config.models import DummyFamily, Geminis, Groks, ModelFamily
from ..data import DataManager
from ..data.conversation import SelectedSproutData
from ..data.conversation.fusion import SproutPackage
from .context import ForestExtractor, TreeExtractor
from .model import Gemini, Grok, Model, launch
from .model.dummy import DummyModel
from .sprout import Sprout


def load_model(sprout: Sprout, param: ModelParam | None = None) -> Model:
    """Create Execution Model from Enum Family Model"""

    model: ModelFamily = sprout.model
    logger.debug(f"Dispatching {model=} with {param=}")

    if isinstance(model, Groks):
        sprout.data.uploader.prepare(target=model.target)
        return Grok(sprout, param)

    if isinstance(model, Geminis):
        sprout.data.uploader.prepare(target=model.target)
        return Gemini(sprout, param)

    if isinstance(model, DummyFamily):
        return DummyModel(sprout, param)

    raise ValueError(f"Unknown {model=}")


class Fire(AbstractContextManager):
    """Lead the CLI execution of the fire command"""

    def __init__(self):
        self.stack: ExitStack[bool | None] = ExitStack()
        self.agents: list[Model] = []

    def __enter__(self) -> Self:
        self.data: DataManager = self.stack.enter_context(DataManager())
        self.forest: ForestExtractor = self.stack.enter_context(
            ForestExtractor(self.data)
        )
        logger.info("ForestExtractor: Stacked to Context")

        self.tree: TreeExtractor = self.stack.enter_context(
            TreeExtractor(data=self.data)
        )
        logger.info("TreeExtractor: Stacked to Context")

        logger.success("capstone.Fire session is ready")
        return self

    def load_models(self, models: list[SelectedSproutData]) -> list[Model]:
        logger.info(f"Start of loading: {models=}")

        self.agents: list[Model] = []

        for model in models:
            package: SproutPackage = self.data.handler.prepare_package(model)
            sprout = Sprout(package, self.data)
            self.agents.append(load_model(sprout))

        logger.info(f"Loaded: {self.agents=}")

        return self.agents

    def launch(self, use_async=False, dry_run=False):
        launch.models(self.agents, use_async, dry_run)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.stack.__exit__(exc_type, exc_val, exc_tb)

    def __repr__(self):
        name = f"{self.__class__.__name__}Contex"
        if hasattr(self.stack, "_exit_callbacks"):
            if isinstance(self.stack._exit_callbacks, deque):
                stack = f"{len(self.stack._exit_callbacks)} Stacks"
        else:
            stack = "Exitstack"
        models = f"{len(self.agents)} loaded Models"
        return f"{name} with {stack} and {models}"

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/sprout.py
from pathlib import Path

from loguru import logger

from ..config import config
from ..config.models import ModelFamily
from ..data import DataManager
from ..data.conversation import Prompt, Response
from ..data.conversation.fusion import SproutPackage

# NEXT:
# NEXT:
# NEXT:
# NEXT:


class Sprout:
    """Runtime Container for 1 Model with DAG SubGraph"""

    def __init__(self, package: SproutPackage, data: DataManager):
        # LATER: attach package and provide properties instead of attach all?
        self.next_response_id: str = package.next_response_id
        self.prompt: Prompt = package.prompt
        self.model: ModelFamily = package.model
        self.previous_remote_id: str | None = package.previous_remote_id
        self.previous_response_uuid: str | None = package.previous_response_id
        self.data: DataManager = data

    def collect_raw_response(self, full_response: str):
        full_response_path: Path = config().paths.full_response(
            topic=self.prompt.topic, model=self.model.unique
        )
        self.data._add_temporary_full_response(
            text=full_response, path=full_response_path
        )

    def collect_response_data(
        self,
        content: str,
        remote_id: str,
        usage: dict,
    ):
        logger.info("collect")
        response = Response(  # Important! override unique_id
            unique_id=self.next_response_id,
            content=content,
            remote_id=remote_id,
            previous_response_id=self.previous_remote_id,
            usage=usage,
            topic=self.prompt.topic,
            sprout_id=self.prompt.sprout_id,
            tree_id=self.prompt.tree_id,
            model=self.model.unique,
        )
        self.data.handle_response(response)

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/__init__.py

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/cli/fire.py
from pathlib import Path

from loguru import logger
from sstcore.cli import sargs
from sstcore.data import SstFile

from ..config import config
from ..core import capstone
from ..core.model import Model
from ..data import DataManager
from ..data.camp import CampManager, UploadFile
from ..data.conversation import SelectedSproutData
from ..exceptions.data import DataRuntimeError
from ..tui import selector
from ..utils.parse import parse_raw_models
from ..utils.print import printer
from . import args
from .canvas.model import model_family_table

DEBUG = True


def fire(
    # Arguments
    models: args.Models = None,
    # sprout: args.Sprout = False, # TODO: some partial select
    # Options for task selection
    pick_role: args.PickRole = True,
    files: sargs.Files = None,
    pick_file: args.PickFile = False,
    images: args.Images = None,
    pick_image: args.PickImage = False,
    # General Options
    use_async: args.Async = False,
    dry_run: sargs.DryRun = False,
    direct_fire: args.Fire = False,
):
    """Prepare Models with Local Prompt and Fire"""

    with capstone.Fire() as session:
        models: list[SelectedSproutData] = _prepare_model_args(session, models)
        agents: list[Model] = session.load_models(models)

        files: list[UploadFile] = _prepare_file_args(
            session.data.camp, files, pick_file
        )
        session.data.load_files(files)

        images: list[SstFile] = _prepare_image_args(
            session.data.camp, images, pick_image
        )
        session.data.handler.prompt.attach_images(images)

        role: Path | None = _prepare_role(pick_role)
        session.data.load_role(role)

        if not direct_fire and not confirm_fire(agents, session.data):
            return

        logger.info("Ready to Fire")

        session.launch(use_async, dry_run)

        printer.success("Models finished to run, storing data, au revoir!")
        printer.title("Paths of generated Files")
        printer(paths := session.data.front.result_files_relative())

        # TODO: improve nvim handling
        printer(f"nvim {' '.join(str(p) for p in paths)}")

    logger.info("All processes finished")


def confirm_fire(models: list[Model], data: DataManager) -> bool:

    printer.special("Summary of Release")

    # LATER:
    # TASK: Prompt Print - including files, images, role

    printer.title(f"Prompt - {(prompt := data.handler.prompt)}")
    printer.md(prompt.content)

    printer.lines_with_len(
        name="Models",
        lines=[model.model.api_name for model in models],
    )

    printer.lines(
        header=f"Role: {prompt.role.path.stem if prompt.role else 'No role selected!'}",
        title="Role",
        lines=[
            prompt.role.content if prompt.role else "build more roles in camp"
        ],
    )

    printer.lines_with_len(
        name="Files",
        lines=[file.name for file in prompt.files],
    )

    printer.lines_with_len(
        name="Images",
        lines=[image.name for image in prompt.images],
    )

    model_family_table(selection=[model.sprout.model for model in models])

    printer.danger("Last check before deployment")

    match input("type 'ok' to launch: "):  # LATER: check rich.prompt.Ask
        case "ok":
            printer.title("send API request now!", style="green")
            return True
        case _:
            printer(
                "see you when prompt and command chain is ready!",
                style="yellow",
            )
            return False  # TASK: id loss?


def _prepare_model_args(
    session: capstone.Fire, models: list[str] | None, multi_select=True
) -> list[SelectedSproutData]:

    printer.debug(
        "Start of Selector",
        session.data.front.models(),
        stop=True,
    )
    printer.title("Model Selection")

    if models and (parsed_models := parse_raw_models(models)):
        text = f"{len(parsed_models)} Models parsed for Pipeline"
        printer.header(text)
        return SelectedSproutData.from_zero(parsed_models)

    match len(scanned_models := session.data.front.models()):  # TEST:
        case 0:
            return SelectedSproutData.from_zero(
                selector.model_family(multi_select=True)
            )
        case 1:
            return [SelectedSproutData.from_scan(scanned_models.pop())]
        case _:
            return selector.model_from_scan(
                models=scanned_models,
                multi_select=multi_select,
            )


def _prepare_file_args(
    camp: CampManager, files: list[Path] | None, pick_file: bool
) -> list[UploadFile]:  # LATER:: as function of camp

    # REFACTOR: files and images, simple function from Camp
    printer.title("Preparing Files...")

    prepared_files: list[UploadFile] = []

    if pick_file:  # Pick first to avoid picking as well new added files
        selected_files: list[Path] = selector.file_registry(files=camp.files)
        for path in selected_files:
            match len(file := camp.files.get_files_by_path(path)):
                case 0:
                    logger.error(f"File not found in UploadRegistry: {path}")
                case 1:
                    file: UploadFile = file[0]
                    prepared_files.append(file)
                    logger.debug(f"added new file: {file.description}")
                case _:
                    logger.error(f"Multiple files with: {path}, {file=}")

    prepared_files.extend(camp.prepare_and_load(files))
    printer.title(f"...{len(prepared_files)} files selected for pipeline")

    return prepared_files


def _prepare_image_args(
    camp: CampManager, images: list[Path] | None, pick_image: bool
) -> list[SstFile]:  # LATER:: as function of camp

    # REFACTOR: files and images, simple function of Camp
    printer.title("Preparing Images...")

    prepared_images: list[SstFile] = []

    if pick_image:  # TODO: use ListSelector? or unify with _prepare_file_args
        selected_images: list[Path] = selector.file_registry(files=camp.images)
        for path in selected_images:
            match len(file := camp.images.get_files_by_path(path)):
                case 0:
                    logger.error(f"File not found in UploadRegistry: {path}")
                case 1:
                    file: SstFile = file[0]
                    prepared_images.append(file)
                    logger.debug(f"added new file: {file.description}")
                case _:
                    logger.error(f"Multiple files with: {path}, {file=}")

    if images:  # Mirror = copy for CLI provided links
        prepared_images.extend(camp.images.mirror_from_path(source=images))

    if (local_files := config().paths.local_file_dir).exists():
        camp.images.absorb_from_path(local_files)

    for image in prepared_images:
        if not image.confirm_local_status(camp.images.local_root):
            raise DataRuntimeError(f"Failed to Import {file=}")

    printer.md(f"...{len(prepared_images)} images selected for pipeline")

    return prepared_images


def _prepare_role(pick_role: bool) -> Path | None:
    # TASK: extend to gathering statistics, creating layouts
    # LATER:: as function of camp

    printer.title("Preparing Role...")

    if pick_role:
        roles: list[Path] = config().paths.role_paths(mode="all")  # PARAM:
        role: Path = selector.role_path(roles)
        logger.info(f"Selected Role: {role.stem}")
    else:
        logger.info("no role selected and no picker")
        role = None

    return role

```

```python
# /home/silvan/PolyBox/Code/sachmis/latest/src/sachmis/core/model/dummy.py
from loguru import logger

from sachmis.config.defaults import ModelParam

from ...config import config
from ...config.models import DummyFamily
from .agent import Model


class DummyModel(Model):
    """sometimes better than grok"""
    model: DummyFamily
    param: ModelParam

    def _load_param(self, param: ModelParam | None):
        self.param: ModelParam = param or ModelParam()

    def _load_client(self):
        logger.info("Client prepared")

    def _prepare_chat(self):
        logger.info("Chat prepared")

    def _attach_role(self, role: str):
        logger.debug(role)

    def _attach_prompt(self, prompt: str):
        if not prompt:
            raise FileNotFoundError("Load proper prompt first!")
        logger.debug("loaded prompt")

    def _attach_images(self):
        for i in self.prompt.images:
            logger.info(i)

    def _attach_files(self):
        for i in self.prompt.files:
            logger.info(i)

    def _get_response(self):
        response: str = """blaa
        xxxxx
        xxxxx
        xxxxx
        xxxxx
        xxxxx
        """
        return response

    def _extract_full_response(self) -> str:
        return str(self._raw_response)

    def _extract_response_content(self) -> str:
        return """# content
        bla
        - test
        ## title
        fdsdfsd
        """

    def _extract_response_id(self) -> str:
        return config().timestamp

    def _extract_usage(self) -> dict | None:
        return {"cost": "a lot"}

    def _calculate_usage_cost(self, usage: dict) -> bool:
        _usage = usage
        return False

```
