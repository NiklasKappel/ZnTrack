"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Simple test for graph execution
"""
import shutil

import pytest
import os
from tempfile import TemporaryDirectory

from zntrack import Node, DVC, PyTrackProject
import numpy as np

temp_dir = TemporaryDirectory()

cwd = os.getcwd()


@Node()
class ComputeA:
    """Node stage A"""

    def __init__(self):
        self.inp = DVC.params()
        self.out = DVC.result()

    def __call__(self, inp):
        self.inp = inp

    def run(self):
        self.out = np.power(2, self.inp).item()


@Node()
class ComputeB:
    """Node stage B"""

    def __init__(self):
        self.inp = DVC.params()
        self.out = DVC.result()

    def __call__(self, inp):
        self.inp = inp

    def run(self):
        self.out = np.power(3, self.inp).item()


@Node()
class ComputeAB:
    """Node stage AB, depending on A&B"""

    def __init__(self):
        self.a = DVC.deps(ComputeA(id_=0))
        self.b = DVC.deps(ComputeB(id_=0))
        self.out = DVC.result()

        self.param = DVC.params()

    def __call__(self):
        self.param = "default"

    def run(self):
        a = ComputeA(id_=0).out
        b = ComputeB(id_=0).out
        self.out = a + b


@Node(name="Stage_A")
class ComputeANamed:
    """Node stage A"""

    def __init__(self):
        self.inp = DVC.params()
        self.out = DVC.result()

    def __call__(self, inp):
        self.inp = inp

    def run(self):
        self.out = np.power(2, self.inp).item()


@Node(name="Stage_AB")
class ComputeABNamed:
    """Node stage AB, depending on A&B with a custom stage name"""

    def __init__(self):
        self.a: ComputeANamed = DVC.deps(ComputeANamed(id_=0))
        self.b: ComputeB = DVC.deps(ComputeB(id_=0))
        self.out = DVC.result()

        self.param = DVC.params()

    def __call__(self):
        self.param = "default"

    def run(self):
        self.out = self.a.out + self.b.out


@pytest.fixture(autouse=True)
def prepare_env():
    """Create temporary directory"""
    temp_dir = TemporaryDirectory()
    shutil.copy(__file__, temp_dir.name)
    os.chdir(temp_dir.name)

    yield

    os.chdir(cwd)
    temp_dir.cleanup()


def test_stage_addition():
    """Check that the dvc repro works"""
    project = PyTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA()
    a(2)
    b = ComputeB()
    b(3)
    ab = ComputeAB()
    ab()

    project.run()
    project.load()
    finished_stage = ComputeAB(id_=0)
    assert finished_stage.out == 31


def test_stage_addition_named():
    """Check that the dvc repro works with named stages"""
    project = PyTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeANamed()
    a(2)
    b = ComputeB()
    b(3)
    ab = ComputeABNamed()
    ab()

    project.repro()
    finished_stage = ComputeABNamed(id_=0)
    assert finished_stage.out == 31


def test_stage_addition_run():
    """Check that the PyTracks run method works"""
    project = PyTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA()
    a(2)
    b = ComputeB()
    b(3)
    ab = ComputeAB()
    ab()

    a.run()
    b.run()
    ab.run()

    finished_stage = ComputeAB(id_=0)
    assert finished_stage.out == 31


def test_stage_addition_named_run():
    """Check that the PyTracks run method works with named stages"""
    project = PyTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeANamed()
    a(2)
    b = ComputeB()
    b(3)
    ab = ComputeABNamed()
    ab()

    ComputeANamed(load=True).run()
    ComputeB(load=True).run()
    ComputeABNamed(load=True).run()

    finished_stage = ComputeABNamed(load=True)
    assert finished_stage.out == 31


def test_named_single_stage():
    """Test a single named stage"""
    project = PyTrackProject()
    project.create_dvc_repository()

    a = ComputeANamed()
    a(2)

    project.repro()

    assert ComputeANamed(load=True).out == 4
