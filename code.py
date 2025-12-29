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

        self.ctrl = self.net.addController(
            'c0',
            controller=RemoteController,
            ip='127.0.0.1',
            port=6633
        )

    def create_topology(self):
        info('*** Adding 5G Core Functions\n')

        self.amf  = self.net.addSwitch('amf',  dpid='0000000000000101')
        self.smf  = self.net.addSwitch('smf',  dpid='0000000000000102')
        self.upf1 = self.net.addSwitch('upf1', dpid='0000000000000103')
        self.upf2 = self.net.addSwitch('upf2', dpid='0000000000000104')
        self.udm  = self.net.addSwitch('udm',  dpid='0000000000000105')
        self.pcf  = self.net.addSwitch('pcf',  dpid='0000000000000106')
        self.ausf = self.net.addSwitch('ausf', dpid='0000000000000107')

        info('*** Adding gNBs\n')
        self.gnbs = []
        for i in range(4):
            dpid = f'{0x200 + i:016x}'
            gnb = self.net.addSwitch(f'gnb{i+1}', dpid=dpid)
            self.gnbs.append(gnb)

        info('*** Adding UEs\n')
        self.ues = []
        for i in range(8):
            ue = self.net.addHost(
                f'ue{i+1}',
                ip=f'10.0.{i+1}.{i+1}/24'
            )
            self.ues.append(ue)

        info('*** Adding servers\n')
        self.mec = self.net.addHost('mec', ip='10.100.1.1/24')
        self.inet = self.net.addHost('inet', ip='10.200.1.1/24')

        info('*** Creating links\n')

        # Core
        self.net.addLink(self.amf, self.smf,  bw=100, delay='1ms')
        self.net.addLink(self.amf, self.upf1, bw=100, delay='1ms')
        self.net.addLink(self.amf, self.upf2, bw=100, delay='1ms')
        self.net.addLink(self.smf, self.upf1, bw=100, delay='1ms')
        self.net.addLink(self.smf, self.upf2, bw=100, delay='1ms')
        self.net.addLink(self.amf, self.udm,  bw=10, delay='2ms')
        self.net.addLink(self.amf, self.pcf,  bw=10, delay='2ms')
        self.net.addLink(self.amf, self.ausf, bw=10, delay='2ms')

        # gNB → AMF
        for i, gnb in enumerate(self.gnbs):
            self.net.addLink(gnb, self.amf, bw=10, delay=f'{5+i}ms')

        # UE → gNB
        for i, ue in enumerate(self.ues):
            gnb = self.gnbs[i % len(self.gnbs)]
            self.net.addLink(ue, gnb, bw=1, delay='10ms')

        # UPF → servers
        self.net.addLink(self.upf1, self.mec,  bw=10, delay='2ms')
        self.net.addLink(self.upf2, self.inet, bw=10, delay='5ms')

    def start(self):
        info('*** Starting network\n')
        self.net.build()
        self.ctrl.start()

        for sw in self.net.switches:
            sw.start([self.ctrl])

        info('*** Testing connectivity\n')
        self.net.pingAll()

    def run(self):
        self.create_topology()
        self.start()
        CLI(self.net)
        self.net.stop()


def main():
    setLogLevel('info')
    FiveGCoreTopology().run()


if __name__ == '__main__':
    main()
