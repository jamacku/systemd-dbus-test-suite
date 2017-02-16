from pydbus import SystemBus

import itertools
import os
import subprocess
import tempfile
import time

import avocado


class TestManager(avocado.Test):
    def setUp(self):
        self.bus = SystemBus()
        self.manager = self.bus.get('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        self.unit = 'test.service'
        self.unit_file =  '/etc/systemd/system/{0}'.format(self.unit)
        self.object_path = '/org/freedesktop/systemd1/unit/test_2eservice'

    def test_AddDependencyUnitFiles(self):
        TARGET = 'multi-user.target'

        with open(self.unit_file, 'w') as u:
            u.write('[Service]\n')
            u.write('ExecStart=/bin/true\n')
            self.manager.Reload()

        force = (True, False)
        runtime = (True, False)
        dependency = ('Wants', 'Requires')
        cases = itertools.product([self.unit], [TARGET], dependency, runtime, force)

        for case in cases:
            prefix = '/run' if case[3] else '/etc'
            sufix = case[2].lower()
            path = '{0}/systemd/system/{1}.{2}/{3}'.format(prefix, TARGET, sufix, self.unit)

            self.log.debug(case)

            changes = self.manager.AddDependencyUnitFiles([case[0]], case[1], case[2], case[3], case[4])
            self.assertEqual(len(changes), 1)

            operation, symlink, target = changes[0]

            self.assertEqual('symlink', operation)
            self.log.debug(path)
            self.log.debug(symlink)
            self.assertEqual(path, symlink)
            self.assertEqual(self.unit_file, target)
            self.assertTrue(os.path.islink(path))

            self.manager.DisableUnitFiles([self.unit], case[3])

    # FOLLOWING 2 TEST CASES BREAK F25. UNCOMMENT ONCE WE BACKPORT FIX FOR #4444
    # def test_CancelJob(self):
    #     with open(self.unit_file, 'w') as u:
    #         u.write('[Service]\n')
    #         u.write('ExecStartPre=/bin/sleep 10\n')
    #         u.write('ExecStart=/bin/true')

    #     self.manager.Reload()

    #     job = self.manager.StartUnit(self.unit, 'replace')
    #     self.log.debug(job)

    #     id = int(job.split('/')[-1])
    #     self.log.debug(id)

    #     self.manager.CancelJob(id)

    #     jobs = self.manager.ListJobs()
    #     self.log.debug(jobs)

    #     self.assertEqual(len(jobs), 0)

    # def test_ClearJobs(self):
    #     with open(self.unit_file, 'w') as u:
    #         u.write('[Service]\n')
    #         u.write('ExecStartPre=/bin/sleep 10\n')
    #         u.write('ExecStart=/bin/true')
    #         self.manager.Reload()

    #     self.manager.StartUnit(self.unit, 'replace')
    #     self.manager.ClearJobs()

    #     jobs = self.manager.ListJobs()
    #     self.assertEqual(len(jobs), 0)

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
        with open(self.unit_file, 'w') as u:
             u.write('[Service]\n')
             u.write('ExecStartPre=/bin/sleep 3600\n')
             u.write('ExecStart=/bin/true')

        self.manager.Reload()
        self.manager.StartUnit(self.unit, 'replace')

        jobs = self.manager.ListJobs()
        self.assertEqual(len(jobs), 1)

        job_id = jobs[0][0]
        expected_job_path = '/org/freedesktop/systemd1/job/{0}'.format(job_id)

        job_path = self.manager.GetJob(job_id)
        self.assertEqual(job_path, expected_job_path)

        self.manager.StopUnit(self.unit, 'replace')

    def test_GetMachineId(self):
        with open('/etc/machine-id', 'r') as f:
            id = f.read().splitlines()[0]

        manager_id = self.manager.GetMachineId()
        self.assertEqual(id, manager_id)

    # def test_Get(self):
    #     self.fail()

    def test_GetUnitByPID(self):
        temp = tempfile.mktemp()
        with open(self.unit_file, 'w') as u:
            u.write('[Service]\n')
            u.write('ExecStart=/bin/bash -c \'echo $$$$ > ' + temp + '; sleep 3600\'\n')
        self.manager.Reload()

        job = self.manager.StartUnit(self.unit, 'replace')
        self.log.debug(job)
        time.sleep(1)

        with open(temp, 'r') as f:
            pid = f.readline()

        obj = self.manager.GetUnitByPID(int(pid))
        self.log.debug(obj)
        self.assertEqual(obj, self.object_path)

        job = self.manager.StopUnit(self.unit, 'replace')
        self.log.debug(job)
        os.remove(temp)

    # def test_GetUnitFileState(self):
    #     self.fail()

    # def test_GetUnit(self):
    #     self.fail()

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

    # def test_LoadUnit(self):
    #     self.fail()

    # def test_MaskUnitFiles(self):
    #     self.fail()

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

    # def test_RestartUnit(self):
    #     self.fail()

    # def test_RevertUnitFiles(self):
    #     self.fail()

    # def test_SetDefaultTarget(self):
    #     self.fail()

    # def test_SetEnvironment(self):
    #     self.fail()

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

    # def test_UnmaskUnitFiles(self):
    #     self.fail()

    # def test_UnsetAndSetEnvironment(self):
    #     self.fail()

    # def test_UnsetEnvironment(self):
    #     self.fail()

    # def test_Unsubscribe(self):
    #     self.fail()

    def tearDown(self):
        try:
            os.remove(self.unit_file)
        except OSError:
            pass

        self.manager.Reload()
