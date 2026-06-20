I will use the regular dunders for debug and log and `__rich__` for creating (probably) 1 template in root with at least 1 subhook for subclasses.
My global `printer` instance will send the final rendered output safely trough `rich.Console`.

I pointed out the concept for my Error handling and Error rendering.

Task to do:

- Check the Levels and Hierarchy below
- Analyze and discuss weak points and potential failures
- Provide ideas for creating plugin-like subclasses
  (especially on Level 3 and 4)

## Level 0

- Just `ProjectError(Exception)`

Responsible for creating Panel with:

- header,title and subtitle: rendered by final error cls-tree and error-msg
- textbox, rendered by subhook implemented by topic and maybe branch,final

Everything such that it provides either a nice rendered result or nothing,
and without causing any additional trouble.

## Level 1 - Branches

Below root I have 3 main branches:

- `launch` B1: attached to `cli.app.SafeTyper`, final layer of defence, handle failing startups and anything that bubbles up
- `task` B2: attached to `core.capstone.TaskExecutor`, handle fails in external calls or internal execution
- `data` B3: attached to `data.manager`, handle fails related to filesystem operations, data processing or validation

Responsible for:

- ensure final catch for master handler on this level
- maybe attach small helptext part to textbox
- name for title or subtitle

## Level 2 - Category

Each Branch has at least 1 category.

- The Idea is to use this as the base factory for any topic

Here is like the bulk of implementation (beside root)

- processing and storing most of the args
- create main help text (including the args)

## Level 3 - BuiltIns

Extend category with builtin Exception for general namespace.

Responsible for:

- Maybe accepting and storing additional args
- name for title or subtitle

So far unsure about order of this and next level, maybe even merging.

## Level 4 - Final

Provide final namespace and input for self explaining Exceptions.

Subclass that points to 1 specific detail of a topic, for example different sublasses inside arboreal.

- The idea is to give the Exception a personalized name and sometimes attaching 1 final detail
- The goal is that the app handling is easier and that the complexity doesn't explodes

Responsible for:

- making wrong assignment in the code directly obvious
  (instead of relying on proper assigning class name args everywhere,
  just provide the Error that has it already and is hard to miss)
- final line of helptext
- name for header inside panel

## Sketch of Class Hierarchy

(The folders are just for visualize, most likely it will end up with 1 folder per branch with 1 file per topic or with 1 file per branch)

```sh
 .
├──  data
│   ├──  arbo
│   │   ├──  file_exists
│   │   │   ├──  biome
│   │   │   ├──  forest
│   │   │   └──  tree
│   │   ├──  file_missing
│   │   │   ├──  biome
│   │   │   ├──  forest
│   │   │   └──  tree
│   │   └──  value_err
│   │       ├──  biome
│   │       ├──  forest
│   │       └──  tree
│   └──  conversation
│       ├──  file_missing
│       │   └──  prompt
│       ├──  runtime_err
│       │   ├──  dag
│       │   ├──  prompt
│       │   └──  response
│       └──  value_err
│           ├──  dag
│           ├──  prompt
│           └──  response
├──  launch
│   ├──  any
│   │   └──  see_what_happens
│   └──  cwd
│       ├──  file_exits
│       ├──  file_missing
│       └──  runtime_err
└──  task
    ├──  api_call
    │   ├──  attribute_err
    │   │   ├──  agent
    │   │   └──  sprout
    │   ├──  runtime_err
    │   │   ├──  agent
    │   │   └──  sprout
    │   └──  value_err
    │       ├──  agent
    │       └──  sprout
    └──  internal
        ├──  runtime_err
        │   ├──  agent
        │   └──  sprout
        └──  value_err
            ├──  agent
            └──  sprout
```

Level 3 and 4 look like interchangeable, i mean 3x4 is the same as 4x3,
as well the responsibilities can switch order or merge if needed.

Still there is **1 concept I want to point out** before starting:

- orthogonal level 3 in between branches

Creating mixin, decorator or something else that "pre-processes" the builtins,
(only if required,not for all, for additional args like f.e. path)
and attaching them in Level 3 or 4.
