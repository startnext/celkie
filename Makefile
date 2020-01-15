up:
	vagrant up celkie

verify: up
	inspec exec test/celike_test.rb \
	  -t ssh://vagrant@127.0.0.1 \
  	-p 2222 \
  	-i .vagrant/machines/celkie/virtualbox/private_key

build:
	docker build -t startnext/celkie:latest .

destroy: 
	vagrant destroy --force

