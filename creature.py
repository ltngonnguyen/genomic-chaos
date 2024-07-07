from enum import Enum
from xml.dom.minidom import getDOMImplementation

import numpy as np

import genome


class MotorType(Enum):
    PULSE = 1
    SINE = 2


class Motor:
    def __init__(self, control_waveform, control_amp, control_freq):
        if control_waveform <= 0.5:
            self.motor_type = MotorType.PULSE
        else:
            self.motor_type = MotorType.SINE
        self.amp = control_amp
        self.freq = control_freq
        self.phase = 0
        self.energy_consumed = 0

    def get_output(self):
        self.phase = (self.phase + self.freq) % (np.pi * 2)
        if self.motor_type == MotorType.PULSE:
            if self.phase < np.pi:
                output = 1
            else:
                output = -1

        if self.motor_type == MotorType.SINE:
            output = np.sin(self.phase)

        # Calculate energy consumption based on output
        self.energy_consumed += abs(output) * self.amp

        return output


class Creature:
    def __init__(self, gene_count):
        self.spec = genome.Genome.get_gene_spec()
        self.dna = genome.Genome.get_random_genome(len(self.spec), gene_count)
        self.flat_links = None
        self.exp_links = None
        self.motors = None
        self.start_position = None
        self.current_position = None
        self.summit = None
        self.energy_consumed = 0

    def set_summit(self, summit):
        self.summit = summit

    def get_flat_links(self):
        if self.flat_links == None:
            gdicts = genome.Genome.get_genome_dicts(self.dna, self.spec)
            self.flat_links = genome.Genome.genome_to_links(gdicts)
        return self.flat_links

    def get_expanded_links(self):
        self.get_flat_links()
        if self.exp_links is not None:
            return self.exp_links

        exp_links = [self.flat_links[0]]
        genome.Genome.expandLinks(
            self.flat_links[0], self.flat_links[0].name, self.flat_links, exp_links
        )
        self.exp_links = exp_links
        return self.exp_links

    def to_xml(self):
        self.get_expanded_links()
        domimpl = getDOMImplementation()
        adom = domimpl.createDocument(None, "start", None)
        robot_tag = adom.createElement("robot")
        for link in self.exp_links:
            robot_tag.appendChild(link.to_link_element(adom))
        first = True
        for link in self.exp_links:
            if first:  # skip the root node!
                first = False
                continue
            robot_tag.appendChild(link.to_joint_element(adom))
        robot_tag.setAttribute("name", "pepe")  #  choose a name!
        return '<?xml version="1.0"?>' + robot_tag.toprettyxml()

    def get_motors(self):
        self.get_expanded_links()
        if self.motors == None:
            motors = []
            for i in range(1, len(self.exp_links)):
                l = self.exp_links[i]
                m = Motor(l.control_waveform, l.control_amp, l.control_freq)
                motors.append(m)
            self.motors = motors
        return self.motors

    def get_distance_travelled(self):
        if self.start_position is None or self.current_position is None:
            return 0.00001
        return np.linalg.norm(
            np.array(self.current_position) - np.array(self.start_position)
        )

    def update_position(self, pos):
        if self.start_position is None:
            self.start_position = pos
        self.current_position = pos

    def finalize_distance(self):
        if self.start_position is None or self.current_position is None:
            return 0
        # Calculate distance to summit at start
        start_to_summit = np.linalg.norm(self.summit - np.array(self.start_position))
        # Calculate distance to summit at end
        end_to_summit = np.linalg.norm(self.summit - np.array(self.current_position))
        # Calculate improvement (reduction in distance to summit)
        distance_improvement = start_to_summit - end_to_summit

        # Calculate total energy consumed by all motors
        self.energy_consumed = sum(motor.energy_consumed for motor in self.get_motors())

        # Calculate fitness based on distance improvement and energy efficiency
        energy_efficiency = distance_improvement / (self.energy_consumed + 1e-6)

        if (
            self.get_distance_travelled() < 0.5
            or energy_efficiency > 1000
            or energy_efficiency < 0.001
        ):
            return distance_improvement
        else:
            return distance_improvement + energy_efficiency

    def update_dna(self, dna):
        self.dna = dna
        self.flat_links = None
        self.exp_links = None
        self.motors = None
        self.start_position = None
        self.last_position = None
        self.energy_consumed = 0
