from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink


class FiveGCoreTopology:
    def __init__(self):
        self.net = Mininet(
            controller=RemoteController,
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True
        )

        # SDN Controller
        self.sdn_controller = self.net.addController(
            name='sdn_ctrl',
            controller=RemoteController,
            ip='127.0.0.1',
            port=6633
        )

    def create_topology(self):
        """Create the complete 5G core topology"""

        # ---------------- Core 5G Functions ----------------
        info('*** Adding 5G Core Functions\n')

        self.amf  = self.net.addSwitch('amf',  dpid='0000000000000101')
        self.smf  = self.net.addSwitch('smf',  dpid='0000000000000102')
        self.upf1 = self.net.addSwitch('upf1', dpid='0000000000000103')
        self.upf2 = self.net.addSwitch('upf2', dpid='0000000000000104')
        self.udm  = self.net.addSwitch('udm',  dpid='0000000000000105')
        self.pcf  = self.net.addSwitch('pcf',  dpid='0000000000000106')
        self.ausf = self.net.addSwitch('ausf', dpid='0000000000000107')

        # ---------------- gNBs ----------------
        info('*** Adding gNBs\n')
        self.gnbs = []

        for i in range(4):
            dpid = f'{0x200 + i:016x}'
            gnb = self.net.addSwitch(f'gnb{i+1}', dpid=dpid)
            self.gnbs.append(gnb)

        # ---------------- UEs ----------------
        info('*** Adding UEs\n')
        self.ues = []

        for i in range(8):
            ue = self.net.addHost(
                name=f'ue{i+1}',
                ip=f'10.0.{i+1}.{i+1}/24',
                mac=f'00:00:00:00:0{i+1}:0{i+1}'
            )
            self.ues.append(ue)

        # ---------------- Cloud / Internet ----------------
        info('*** Adding cloud servers\n')

        self.mec_server = self.net.addHost(
            'mec_server',
            ip='10.100.1.1/24',
            mac='00:00:00:00:fe:01'
        )

        self.internet_gw = self.net.addHost(
            'internet_gw',
            ip='10.200.1.1/24',
            mac='00:00:00:00:ff:01'
        )

        # ---------------- Links with QoS ----------------
        info('*** Creating links with QoS\n')

        # Core network links (high capacity, low latency)
        self.net.addLink(self.amf, self.smf,  bw=100, delay='1ms')
        self.net.addLink(self.amf, self.upf1, bw=100, delay='1ms')
        self.net.addLink(self.amf, self.upf2, bw=100, delay='1ms')
        self.net.addLink(self.smf, self.upf1, bw=100, delay='1ms')
        self.net.addLink(self.smf, self.upf2, bw=100, delay='1ms')
        self.net.addLink(self.amf, self.udm,  bw=10,  delay='2ms')
        self.net.addLink(self.amf, self.pcf,  bw=10,  delay='2ms')
        self.net.addLink(self.amf, self.ausf, bw=10,  delay='2ms')

        # gNB → AMF
        for i, gnb in enumerate(self.gnbs):
            self.net.addLink(
                gnb,
                self.amf,
                bw=10,
                delay=f'{5 + i}ms'
            )

        # UE → gNB (radio access)
        for i, ue in enumerate(self.ues):
            gnb_index = i % len(self.gnbs)
            self.net.addLink(
                ue,
                self.gnbs[gnb_index],
                bw=1,
                delay=f'{10 + gnb_index}ms'
            )

        # UPF → Cloud
        self.net.addLink(self.upf1, self.mec_server, bw=10, delay='2ms')
        self.net.addLink(self.upf2, self.internet_gw, bw=10, delay='5ms')

    def start_network(self):
        """Start the network"""
        info('*** Starting network\n')

        self.net.build()
        self.sdn_controller.start()

        for sw in self.net.switches:
            sw.start([self.sdn_controller])

        info('*** Testing connectivity\n')
        self.net.pingAll()

    def run_performance_tests(self):
        """Run basic 5G performance tests"""
        info('*** Running performance tests\n')

        info('*** UE1 → MEC bandwidth test\n')
        self.ues[0].cmd(
            'iperf3 -c 10.100.1.1 -t 10 > ue1_mec.txt &'
        )

        info('*** Latency tests\n')
        for i, ue in enumerate(self.ues[:3]):
            result = ue.cmd('ping -c 5 10.100.1.1')
            info(f'Latency UE{i+1} → MEC:\n{result}\n')

    def run(self):
        self.create_topology()
        self.start_network()
        self.run_performance_tests()
        CLI(self.net)
        self.net.stop()


def main():
    setLogLevel('info')
    topology = FiveGCoreTopology()
    topology.run()


if __name__ == '__main__':
    main()
