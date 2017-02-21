import itertools
import os
import resource
import subprocess
import tempfile
import time
import unittest

import avocado

from pydbus import SystemBus

class TestManager(avocado.Test):
    def setUp(self):
        self.bus = SystemBus()
        self.manager = self.bus.get("org.freedesktop.systemd1", "/org/freedesktop/systemd1")
        self.unit = "test.service"
        self.unit_file = "/etc/systemd/system/{0}".format(self.unit)
        self.unit_object_path = "/org/freedesktop/systemd1/unit/test_2eservice"
        self.cleanup_files = [self.unit_file]
        self.cleanup_environment = []

        with open(self.unit_file, "w") as u:
            u.write("[Service]\n")
            u.write("ExecStart=/usr/bin/true\n")
        self.manager.Reload()

    def test_AddDependencyUnitFiles(self):
        TARGET = "multi-user.target"

        force = (True, False)
        runtime = (True, False)
        dependency = ("Wants", "Requires")
        cases = itertools.product([self.unit], [TARGET], dependency, runtime, force)

        for case in cases:
            prefix = "/run" if case[3] else "/etc"
            sufix = case[2].lower()
            path = "{0}/systemd/system/{1}.{2}/{3}".format(prefix, TARGET, sufix, self.unit)

            self.log.debug(case)

            changes = self.manager.AddDependencyUnitFiles([case[0]], case[1], case[2], case[3], case[4])
            self.assertEqual(len(changes), 1)

            operation, symlink, target = changes[0]

            self.assertEqual("symlink", operation)
            self.log.debug(path)
            self.log.debug(symlink)
            self.assertEqual(path, symlink)
            self.assertEqual(self.unit_file, target)
            self.assertTrue(os.path.islink(path))

            self.manager.DisableUnitFiles([self.unit], case[3])

    def test_CancelJob(self):
        with open(self.unit_file, "w") as u:
            u.write("[Service]\n")
            u.write("ExecStartPre=/bin/sleep 10\n")
            u.write("ExecStart=/bin/true")

        self.manager.Reload()

        job = self.manager.StartUnit(self.unit, "replace")
        self.log.debug(job)

        id = int(job.split("/")[-1])
        self.log.debug(id)

        self.manager.CancelJob(id)

        jobs = self.manager.ListJobs()
        self.log.debug(jobs)

        self.assertEqual(len(jobs), 0)
        self.manager.StopUnit(self.unit, "replace")

    def test_ClearJobs(self):
        with open(self.unit_file, "w") as u:
            u.write("[Service]\n")
            u.write("ExecStartPre=/bin/sleep 10\n")
            u.write("ExecStart=/bin/true")
            self.manager.Reload()

        self.manager.StartUnit(self.unit, "replace")
        self.manager.ClearJobs()

        jobs = self.manager.ListJobs()
        self.assertEqual(len(jobs), 0)
        self.manager.StopUnit(self.unit, "replace")

    # def test_DisableUnitFiles(self):
    #     self.fail()

    # def test_Dump(self):
    #     self.fail()

    # def test_EnableUnitFiles(self):
    #     self.fail()

    # def test_Exit(self):
    #     self.fail()

    # def test_GetAll(self):
    #     self.fail()

    # def test_GetDefaultTarget(self):
    #     self.fail()

    def test_GetJob(self):
        with open(self.unit_file, "w") as u:
             u.write("[Service]\n")
             u.write("ExecStartPre=/bin/sleep 3600\n")
             u.write("ExecStart=/bin/true")

        self.manager.Reload()
        self.manager.StartUnit(self.unit, "replace")

        jobs = self.manager.ListJobs()
        self.assertEqual(len(jobs), 1)

        job_id = jobs[0][0]
        expected_job_path = "/org/freedesktop/systemd1/job/{0}".format(job_id)

        job_path = self.manager.GetJob(job_id)
        self.assertEqual(job_path, expected_job_path)

        self.manager.StopUnit(self.unit, "replace")

    def test_GetMachineId(self):
        with open("/etc/machine-id", "r") as f:
            id = f.read().splitlines()[0]

        manager_id = self.manager.GetMachineId()
        self.assertEqual(id, manager_id)

    def test_Get(self):
        """ Test Get() on basic manager properties.
        """
        p = self.manager.Get("org.freedesktop.systemd1.Manager", "Version")
        # Version is the second word on the first line in the output.
        v = subprocess.check_output(["systemctl", "--version"]).split("\n")[0].split()[1]
        self.assertEqual(p, v)

        config = {"LogLevel": "info",
                  "LogTarget": "journal-or-kmsg"}
        for (prop, val) in config.iteritems():
            p = self.manager.Get("org.freedesktop.systemd1.Manager", prop)
            self.assertEqual(p, val)

        for prop in ["DefaultLimitCPU",
                     "DefaultLimitFSIZE",
                     "DefaultLimitDATA",
                     "DefaultLimitSTACK",
                     "DefaultLimitCORE",
                     "DefaultLimitRSS",
                     "DefaultLimitAS",
                     "DefaultLimitLOCKS",
                     "DefaultLimitRTTIME"]:
            p = self.manager.Get("org.freedesktop.systemd1.Manager", prop)
            l = 2 ** 64 - 1
            self.assertEqual(p, l)

        config = {"DefaultLimitNOFILE": resource.getrlimit(resource.RLIMIT_NOFILE)[1],
                  "DefaultLimitNPROC": resource.getrlimit(resource.RLIMIT_NPROC)[1],
                  "DefaultLimitMEMLOCK": resource.getrlimit(resource.RLIMIT_MEMLOCK)[1],
                  # The following limits don"t have symbolic values in Python 2.7.
                  # Use the ones from /usr/include/bits/resource.h.
                  "DefaultLimitSIGPENDING": resource.getrlimit(11)[1],
                  "DefaultLimitMSGQUEUE": resource.getrlimit(12)[1],
                  "DefaultLimitRTPRIO": resource.getrlimit(14)[1]}
        for (prop, val) in config.iteritems():
            p = self.manager.Get("org.freedesktop.systemd1.Manager", prop)
            self.assertEqual(p, val)


    def test_GetUnitByPID(self):
        temp = tempfile.mktemp()
        self.cleanup_files += [temp]
        with open(self.unit_file, "w") as u:
            u.write("[Service]\n")
            u.write("ExecStart=/bin/bash -c \"echo $$$$ > " + temp + "; sleep 3600\"\n")
        self.manager.Reload()

        job = self.manager.StartUnit(self.unit, "replace")
        self.log.debug(job)
        time.sleep(1)

        with open(temp, "r") as f:
            pid = f.readline()

        obj = self.manager.GetUnitByPID(int(pid))
        self.log.debug(obj)
        self.assertEqual(obj, self.unit_object_path)

        job = self.manager.StopUnit(self.unit, "replace")
        self.log.debug(job)

    def test_GetUnitFileState(self):
        TARGET = "multi-user.target"

        with open(self.unit_file, "w") as u:
             u.write("[Service]\n")
             u.write("ExecStart=/bin/true\n")

        self.manager.Reload()

        # unit file doesn"t have [Install] section, hence it should be marked as static
        state = self.manager.GetUnitFileState(self.unit)
        self.assertEqual(state, "static")

        # after we add wants dependency to multi-user.target it should be marked as enabled
        self.manager.AddDependencyUnitFiles([self.unit], TARGET, "Wants", False, False)
        state = self.manager.GetUnitFileState(self.unit)
        self.assertEqual(state, "enabled")

        # when we disable the unit, then state should be again static
        self.manager.DisableUnitFiles([self.unit], False)
        state = self.manager.GetUnitFileState(self.unit)
        self.assertEqual(state, "static")

        with open(self.unit_file, "a") as u:
             u.write("[Install]\n")
             u.write("WantedBy=multi-user.target\n")

        self.manager.Reload()

        # we added [Install] section but unit file is not enabled
        state = self.manager.GetUnitFileState(self.unit)
        self.assertEqual(state, "disabled")

    def test_GetUnit(self):
        with open(self.unit_file, "w") as u:
            u.write("[Service]\n")
            u.write("ExecStart=/bin/sleep 5\n")
            self.manager.Reload()


        self.manager.StartUnit(self.unit, "replace")
        result = self.manager.GetUnit(self.unit)
        self.assertEqual(result, self.unit_object_path)


    # def test_GetUnitProcesses(selfelf):
    #     self.fail()

    # def test_Halt(self):
    #     self.fail()

    # def test_Introspect(self):
    #     self.fail()

    # def test_KExec(self):
    #     self.fail()

    # def test_KillUnit(self):
    #     self.fail()

    # def test_LinkUnitFiles(self):
    #     self.fail()

    # def test_ListJobs(self):
    #     self.fail()

    # def test_ListUnitFilesByPatterns(self):
    #     self.fail()

    # def test_ListUnitFiles(self):
    #     self.fail()

    # def test_ListUnitsByNames(self):
    #     self.fail()

    # def test_ListUnitsByPatterns(self):
    #     self.fail()

    # def test_ListUnitsFiltered(self):
    #     self.fail()

    # def test_ListUnits(self):
    #     self.fail()

    def test_LoadUnit(self):
        with open(self.unit_file, "w") as u:
            u.write("[Service]\n")
            u.write("ExecStart=/bin/sleep 5\n")
            self.manager.Reload()
        result = self.manager.LoadUnit(self.unit)
        self.assertEqual(result, self.unit_object_path)


    def test_MaskUnitFiles_UnmaskUnitFiles(self):
        # We can't mask stuff from /etc
        unit = "test2.service"
        unit_file =  "/usr/lib/systemd/system/{0}".format(unit)
        self.cleanup_files += [unit_file]
        with open(unit_file, "w") as u:
             u.write("[Service]\n")
             u.write("ExecStart=/bin/true\n")

        self.manager.Reload()

        force = (True, False)
        runtime = (True, False)
        cases = itertools.product(runtime, force)

        for case in cases:
            prefix = "/run" if case[0] else "/etc"
            path = "{0}/systemd/system/{1}".format(prefix, unit)

            if case[1]:
                os.symlink("/tmp/foo", path)
                changes_num = 2
            else:
                changes_num = 1

            changes = self.manager.MaskUnitFiles([unit], case[0], case[1])
            self.assertEqual(len(changes), changes_num)
            self.assertEqual(os.readlink(path), "/dev/null")

            changes = self.manager.UnmaskUnitFiles([unit], case[0])
            self.assertEqual(len(changes), 1)
            self.assertFalse(os.path.islink(path))

    def test_Ping(self):
        self.manager.Ping()

    # def test_PowerOff(self):
    #     self.fail()

    # def test_PresetAllUnitFiles(self):
    #     self.fail()

    # def test_PresetUnitFiles(self):
    #     self.fail()

    # def test_PresetUnitFilesWithMode(self):
    #     self.fail()

    # def test_Reboot(selfelf):
    #     self.fail()

    # def test_ReenableUnitFiles(self):
    #     self.fail()

    # def test_Reexecute(self):
    #     self.fail()

    # def test_Reload(self):
    #     self.fail()

    # def test_ReloadOrRestartUnit(self):
    #     self.fail()

    # def test_ReloadOrTryRestartUnit(self):
    #     self.fail()

    # def test_ReloadUnit(self):
    #     self.fail()

    # def test_RemoveSnapshot(self):
    #     self.fail()

    # def test_ResetFailed(self):
    #     self.fail()

    # def test_ResetFailedUnit(self):
    #     self.fail()

    def test_RestartUnit(self):
        temporary_file_1 = tempfile.mktemp()
        temporary_file_2 = tempfile.mktemp()
        with open(self.unit_file, "w") as u:
            u.write("[Service]\n")
            u.write("Type=oneshot\n")
            u.write("RemainAfterExit=True\n")
            u.write("ExecStart=/bin/bash -c \'echo \"Unit has started\" >> " + temporary_file_1 + "\'\n")
            u.write("ExecStop=/bin/bash -c \'echo \"Unit has finished\" >> " + temporary_file_2 + "\'\n")
        self.manager.Reload()

        # Let the unit write some lines
        self.manager.RestartUnit(self.unit, "replace")
        time.sleep(1)
        line_count_1 = 0
        with open(temporary_file_1, "r") as f:
            for _ in f:
                line_count_1 += 1

        line_count_2 = 0


        self.assertEqual(1, line_count_1)
        self.assertTrue(not os.path.exists(temporary_file_2))

        self.manager.RestartUnit(self.unit, "replace")
        time.sleep(1)
        line_count_1 = 0
        with open(temporary_file_1, "r") as f:
            for _ in f:
                line_count_1 += 1

        line_count_2 = 0
        with open(temporary_file_2, "r") as f:
            for _ in f:
                line_count_2 += 1

        self.assertEqual(2, line_count_1)
        self.assertEqual(1, line_count_2)
        self.manager.StopUnit(self.unit, "replace")
        self.cleanup_files+=[temporary_file_1]
        self.cleanup_files+=[temporary_file_2]





    # def test_RevertUnitFiles(self):
    #     self.fail()

    # def test_SetDefaultTarget(self):
    #     self.fail()

    def prepare_environment(self):
        """
        Write a testing unit which will dump its environment to a temporary file when started.
        Return the temporary file"s path.
        """
        temp = tempfile.mktemp()
        self.cleanup_files += [temp]
        body = "[Service]\nExecStart=/usr/bin/bash -c '/usr/bin/env > {}'".format(temp)
        with open(self.unit_file, "w") as u:
            u.write(body)
        self.manager.Reload()
        return temp

    def test_SetEnvironment(self):
        """
        First, get the default manager environment. Safety check that it"s visible from the testing
        unit. Set some environment variables and check if they are readable from the testing unit.
        """
        temp = self.prepare_environment()
        self.cleanup_environment += ["FOO", "BOO"]

        # The manager"s default environment.
        env = self.manager.Get("org.freedesktop.systemd1.Manager", "Environment")

        # The unit"s environment as pass from the manager.
        self.manager.StartUnit(self.unit, "replace")
        time.sleep(0.5)
        unit_env = ""
        with open(temp, "r") as t:
            unit_env = t.read().splitlines()

        # All the defaults as retrieved from the manager should be present in the unit"s enviroment
        # without change.
        for assignment in env:
            self.assertTrue(assignment in unit_env)

        test_env = ["FOO=this-is-never-going-to-be-there", "BOO=1234"]
        self.manager.SetEnvironment(test_env)

        self.manager.StartUnit(self.unit, "replace")
        time.sleep(0.5)

        # Now all the defaults plus the set environment should be present in the unit"s environment.
        unit_env = ""
        with open(temp, "r") as t:
            unit_env = t.read().splitlines()
        for assignment in env + test_env:
            self.assertTrue(assignment in unit_env)

        self.manager.SetEnvironment([])

    # def test_SetExitCode(self):
    #     self.fail()

    # def test_Set(self):
    #     self.fail()

    # def test_SetUnitProperties(self):
    #     self.fail()

    # def test_StartTransientUnit(self):
    #     self.fail()

    # def test_StartUnit(self):
    #     self.fail()

    # def test_StartUnitReplace(self):
    #     self.fail()

    # def test_StopUnit(self):
    #     self.fail()

    # def test_Subscribe(self):
    #     self.fail()

    # def test_SwitchRoot(self):
    #     self.skip()

    # def test_TryRestartUnit(self):
    #     self.fail()

    # def test_UnsetAndSetEnvironment(self):
    #     self.fail()

    def test_UnsetEnvironment(self):
        """
        Set a dummy environment. After safety checking that the dummy environment exists, unset it.
        """
        temp = self.prepare_environment()
        self.cleanup_environment += ["_UNSET_TEST"]

        test_env = ["_UNSET_TEST=unset-me-please"]
        self.manager.SetEnvironment(test_env)

        self.manager.StartUnit(self.unit, "replace")
        time.sleep(0.5)

        # Make sure that the test unit sees the set environment.
        unit_env = ""
        with open(temp, "r") as t:
            unit_env = t.read().splitlines()
        for assignment in test_env:
            self.assertTrue(assignment in unit_env)

        self.manager.UnsetEnvironment(["_UNSET_TEST"])

        self.manager.StartUnit(self.unit, "replace")
        time.sleep(0.5)
        unit_env = ""
        with open(temp, "r") as t:
            unit_env = t.read().splitlines()

        self.assertTrue(test_env not in unit_env)
        self.manager.UnsetEnvironment([])


    # def test_Unsubscribe(self):
    #     self.fail()

    def tearDown(self):
        try:
            self.manager.StopUnit(self.unit, "replace")
            time.sleep(0.25)
        except:
            pass

        for f in self.cleanup_files:
            try:
                os.remove(f)
            except OSError:
                pass

        self.manager.UnsetEnvironment(self.cleanup_environment)
        self.manager.Reload()

if __name__ == "__main__":
    unittest.main()
