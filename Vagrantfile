$dependencies = <<SCRIPT
if ! docker info; then
  curl -fsSL get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker vagrant
fi

apt install --yes python3-docopt python3-docker python3-pip

apt update
apt -y install software-properties-common
apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0xF1656F24C74CD1D8
add-apt-repository -y 'deb [arch=amd64,arm64,ppc64el] http://mirror.23media.de/mariadb/repo/10.1/ubuntu bionic main'
apt update
debconf-set-selections <<< "maria-db-server-10.1 mysql-server/root_password password foobar"
debconf-set-selections <<< "maria-db-server-10.1 mysql-server/root_password_again password foobar"
apt install -y mariadb-server-10.1 mariadb-backup-10.1

SCRIPT

$example_db = <<SCRIPT
# We don't do anything if the example sakila database is already there.
if [[ ! $(mysql -u root -pfoobar -e "SHOW DATABASES LIKE 'sakila'") ]]; then
  mysql -s -N -e
  wget https://downloads.mysql.com/docs/sakila-db.tar.gz -P /tmp
  tar -xvzf /tmp/sakila-db.tar.gz -C /tmp
  mysql -u root -pfoobar < /tmp/sakila-db/sakila-schema.sql
  mysql -u root -pfoobar < /tmp/sakila-db/sakila-data.sql
else
  echo 'Example database already in place.'
fi

SCRIPT

Vagrant.configure(2) do |config|
  config.vm.define "celkie" do |machine|
    machine.vm.box = "ubuntu/bionic64"
    machine.vm.provision "shell", inline: $dependencies
    machine.vm.provision "shell", inline: $example_db
    machine.vm.network "forwarded_port", guest: 13360, host: 13360
  end
end
