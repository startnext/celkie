describe command('celkie backup') do
  its('exit_status') { should eq 0 }
  its('stdout') { should match '.*completed OK!' }
end

describe command('celkie list') do
  its('exit_status') { should eq 0 }
  its('stdout') { should match '.*_full' }
end

describe command('celkie backup --database sakila') do
  its('exit_status') { should eq 0 }
  its('stdout') { should match '.*completed OK!' }
end

get_last_full_backup = command("celkie list | grep -oP '.*[0-9]{6}_full$' | tail -1" )

describe get_last_full_backup do
  its('exit_status') { should cmp 0 }
  its('stdout') { should match '.*[0-9]{6}_full$' }
end

describe command('celkie dump --backup ' + get_last_full_backup.stdout.strip) do
  its('exit_status') { should eq 0 }
  its('stdout') { should match '.*completed OK!' }
  its('stdout') { should match '.*Database dump created.*' }
end

describe docker_container('celkie-mariadb') do
  it { should_not exist }
end

describe command('celkie dump --backup ' + get_last_full_backup.stdout.strip + ' --database sakila') do
  its('exit_status') { should eq 0 }
  its('stdout') { should match '.*completed OK!' }
  its('stdout') { should match '.*Database dump created.*' }
end

describe docker_container('celkie-mariadb') do
  it { should_not exist }
end

describe command('celkie dump --backup ' + get_last_full_backup.stdout.strip + ' --database sakila' + ' --table film actor city') do
  its('exit_status') { should eq 0 }
  its('stdout') { should match '.*completed OK!' }
  its('stdout') { should match '.*Database dump created.*' }
end

describe docker_container('celkie-mariadb') do
  it { should_not exist }
end

