'''
Notices:
Copyright 2018 United States Government as represented by the Administrator of
the National Aeronautics and Space Administration. No copyright is claimed in
the United States under Title 17, U.S. Code. All Other Rights Reserved.

Disclaimers
No Warranty: THE SUBJECT SOFTWARE IS PROVIDED "AS IS" WITHOUT ANY WARRANTY OF
ANY KIND, EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
TO, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY
IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR
FREEDOM FROM INFRINGEMENT, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL BE ERROR
FREE, OR ANY WARRANTY THAT DOCUMENTATION, IF PROVIDED, WILL CONFORM TO THE
SUBJECT SOFTWARE. THIS AGREEMENT DOES NOT, IN ANY MANNER, CONSTITUTE AN
ENDORSEMENT BY GOVERNMENT AGENCY OR ANY PRIOR RECIPIENT OF ANY RESULTS,
RESULTING DESIGNS, HARDWARE, SOFTWARE PRODUCTS OR ANY OTHER APPLICATIONS
RESULTING FROM USE OF THE SUBJECT SOFTWARE.  FURTHER, GOVERNMENT AGENCY
DISCLAIMS ALL WARRANTIES AND LIABILITIES REGARDING THIRD-PARTY SOFTWARE, IF
PRESENT IN THE ORIGINAL SOFTWARE, AND DISTRIBUTES IT "AS IS."

Waiver and Indemnity:  RECIPIENT AGREES TO WAIVE ANY AND ALL CLAIMS AGAINST THE
UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS ANY
PRIOR RECIPIENT.  IF RECIPIENT'S USE OF THE SUBJECT SOFTWARE RESULTS IN ANY
LIABILITIES, DEMANDS, DAMAGES, EXPENSES OR LOSSES ARISING FROM SUCH USE,
INCLUDING ANY DAMAGES FROM PRODUCTS BASED ON, OR RESULTING FROM, RECIPIENT'S
USE OF THE SUBJECT SOFTWARE, RECIPIENT SHALL INDEMNIFY AND HOLD HARMLESS THE
UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS ANY
PRIOR RECIPIENT, TO THE EXTENT PERMITTED BY LAW.  RECIPIENT'S SOLE REMEDY FOR
ANY SUCH MATTER SHALL BE THE IMMEDIATE, UNILATERAL TERMINATION OF THIS
AGREEMENT.
'''

import h5py
import os
from ..particles.particle import Particle
from ..smc.smc_step import SMCStep


class HDF5Storage(object):

    def __init__(self, h5_filename, mode):
        '''
        :param h5_filename: name of hdf5 file in which to save or from which
            to load a particle, a collection of particles, referred to as a
            particle step, or collection of steps, referred to as a particle
            chain.
        :type h5_filename: string
        :param mode: mode used when opening hdf5 file specified by h5_filename;
            can be 'w', 'r', 'r+', or 'a'. See h5py docs for details.
        :type mode: string
        '''
        self._h5 = h5py.File(h5_filename, mode=mode)
        self._mode = mode
        if 'steps' not in self._h5:
            self._step_parent_grp = self._h5.create_group('steps')
        else:
            self._step_parent_grp = self._h5['steps']

    def close(self,):
        self._h5.close()
        return None

    def get_num_steps(self,):
        '''
        Returns number of steps currently stored in the hdf5 file.
        '''
        return len(self._step_parent_grp.keys())

    def get_num_particles_in_step(self, step_index):
        '''
        Returns the number of particles in a particular step.

        :param step_index: index of step that the particle belongs too
        :type step_index: integer
        '''
        step_name = 'step_{0:03}'.format(step_index)
        return len(self._step_parent_grp[step_name].keys())

    def write_particle(self, particle, step_index, particle_index):
        '''
        Writes a single particle object (params, weight and log likelihood)
        to the hdf5 file.

        :param particle: particle object storing a single parameter vector and
            associated weight and log likelihood.
        :type particle: Particle class instance
        :param step_index: index of step that the particle belongs too
        :type step_index: integer
        :param particle_index: index of particle within a given step
        :type particle_index: integer
        '''
        step_name = 'step_{0:03}'.format(step_index)
        particle_name = 'particle_%s' % particle_index
        if step_name not in self._step_parent_grp:
            self._create_step_group(step_index)
        step_grp = self._step_parent_grp[step_name]
        particle_grp = step_grp.create_group(particle_name)
        self._write_particle_params(particle.params, particle_grp)
        self._write_particle_log_weight(particle.log_weight, particle_grp)
        self._write_particle_log_like(particle.log_like, particle_grp)
        return None

    def read_particle(self, step_index, particle_index):
        '''
        Loads and returns a particle identified by specific step and particle
        indices.

        :param step_index: index of step that the particle belongs too
        :type step_index: integer
        :param particle_index: index of particle within a given step
        :type particle_index: integer
        '''
        particle_grp = self._get_particle_group(step_index, particle_index)
        log_weight = particle_grp['log_weight'][()]
        log_like = particle_grp['log_like'][()]
        params_grp = particle_grp['parameters']
        params = {key: params_grp[key][()] for key in params_grp.keys()}
        particle = Particle(params, log_weight, log_like)
        return particle

    def write_step(self, step, step_index):
        '''
        Writes a step, which is a collection of particles, to the hdf5 file.

        :param step: a list of particle objects, each of which stores a single
            parameter vector and associated weight and log likelihood.
        :type step: list of Particle class instances
        :param step_index: index of step being written
        :type step_index: integer
        '''
        self._create_step_group(step_index)
        for particle_index, particle in enumerate(step.particles):
            self.write_particle(particle, step_index, particle_index)
        return None

    def read_step(self, step_index):
        '''
        Loads and returns a step (and all particles in that step) identified by         a specific step index.

        :param step_index: index of step that the particle belongs too
        :type step_index: integer
        '''
        step_grp = self._get_step_group(step_index)
        step = SMCStep()
        for particle_name in step_grp.keys():
            particle_index = int(particle_name.split('_')[-1])
            step.add_particle(self.read_particle(step_index, particle_index))
        return step

    def write_step_list(self, step_list):
        '''
        Write a step list, which is a list of steps, each of which being a
        list of particles, to the hdf5 file.

        :param particle_chain: a list of steps, each of which is a list of
            particle objects.
        :type step_list: list of SMCStep classes
        '''
        for step_index, step in enumerate(step_list):
            self.write_step(step, step_index + 1)
        return None

    def read_step_list(self,):
        '''
        Loads and returns an entire step list (which consists of all
        available steps and particles within each step).
        '''
        step_list = []
        for step_name in self._step_parent_grp.keys():
            step_index = int(step_name.split('_')[-1])
            step = self.read_step(step_index)
            step_list.append(step)
        return step_list

    def _create_step_group(self, step_index):
        self._step_parent_grp.create_group('step_{0:03}'.format(step_index))
        return None

    def _write_particle_params(self, params, particle_grp):
        parameters_grp = particle_grp.create_group('parameters')
        for key, value in params.iteritems():
            parameters_grp.create_dataset(key, data=value, dtype=float)
        return None

    def _write_particle_log_weight(self, log_weight, particle_grp):
        particle_grp.create_dataset('log_weight', data=log_weight)
        return None

    def _write_particle_log_like(self, log_like, particle_grp):
        particle_grp.create_dataset('log_like', data=log_like)
        return None

    def _get_particle_group(self, step_index, particle_index):
        step_name = 'step_{0:03}'.format(step_index)
        particle_name = 'particle_%s' % particle_index
        path = os.path.join(step_name, particle_name)
        return self._step_parent_grp[path]

    def _get_step_group(self, step_index):
        step_name = 'step_{0:03}'.format(step_index)
        return self._step_parent_grp[step_name]
