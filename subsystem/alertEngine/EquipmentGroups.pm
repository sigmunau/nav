# EquipmentGroups.pm
#
# Class that contains information about all available equipment groups
#
# Arne �sleb�, UNINETT, 2002
#

package EquipmentGroups;

use strict;
use IP;
use Log;

#my $dbh;
#my %info;

sub new
#Constructor
  {
    my $this={};
    shift;
    $this->{dbh}=shift;

    #Access control fields
    $this->{datatype}{string}=0;
    $this->{datatype}{int}=1;
    $this->{datatype}{ip}=2;
    
    #Access control type
    $this->{type}{eq}=0;
    $this->{type}{more}=1;
    $this->{type}{moreeq}=2;
    $this->{type}{less}=3;
    $this->{type}{lesseq}=4;
    $this->{type}{neq}=5;
    $this->{log}=Log->new();
    bless $this;
    $this->collectInfo();
    return $this;
  }

sub collectInfo()
#Collects all relevant information
#Returns true if successful.
  {
    my $this=shift;

    my $egs=$this->{dbh}->selectall_arrayref("select id,accountid from utstyrgruppe");

    if($DBI::errstr)
      {
	$this->{log}->printlog("EquipmentGroups","collectInfo",$Log::error,"could not get list of equipment groups");
	return 0;
      }

    foreach my $eg (@$egs)
      {
	$this->{info}[$eg->[0]]->{user}=$eg->[1];
	my $efs=$this->{dbh}->selectall_arrayref("select uf.id, uf.accountid, gtf.inkluder, gtf.prioritet from utstyrgruppe ug,gruppetilfilter gtf, utstyrfilter uf where ug.id=$eg->[0] and ug.id=gtf.utstyrgruppeid and uf.id=gtf.utstyrfilterid order by gtf.prioritet");
	
	if($DBI::errstr)
	  {
	      $this->{log}->printlog("EquipmentGroups","collectInfo",$Log::error,"could not get list of equipment filters\n");
	    return 0;
	  }

	my $c=0;
	foreach my $ef (@$efs)
	  {
	    $this->{info}[$eg->[0]]->{filters}[$c]->{userid}=$ef->[1];
	    $this->{info}[$eg->[0]]->{filters}[$c]->{included}=$ef->[2];
	    $this->{info}[$eg->[0]]->{filters}[$c]->{priority}=$ef->[3];

	    my $fms=$this->{dbh}->selectall_arrayref("select fm.id,fm.matchfelt,fm.matchtype,fm.verdi,mf.valueid,mf.valuename,mf.datatype from filtermatch fm,utstyrfilter uf,matchfield mf where fm.utstyrfilterid=uf.id and uf.id=$ef->[0] and fm.matchfelt=mf.matchfieldid");
	
	    if($DBI::errstr)
	      {
		  $this->{log}->printlog("EquipmentGroups","collectInfo",$Log::error,"could not get list of equipment filters\n");
		return 0;
	      }
	
	    my $c2=0;
	    foreach my $fm (@$fms)
	      {
		$this->{info}[$eg->[0]]->{filters}[$c]->{filterMatch}[$c2]->{field}=$fm->[1];
		$this->{info}[$eg->[0]]->{filters}[$c]->{filterMatch}[$c2]->{type}=$fm->[2];
		$this->{info}[$eg->[0]]->{filters}[$c]->{filterMatch}[$c2]->{value}=$fm->[3];
		$this->{info}[$eg->[0]]->{filters}[$c]->{filterMatch}[$c2]->{valueid}=$fm->[4];
		$this->{info}[$eg->[0]]->{filters}[$c]->{filterMatch}[$c2]->{valuename}=$fm->[5];
		$this->{info}[$eg->[0]]->{filters}[$c]->{filterMatch}[$c2]->{datatype}=$fm->[6];
		$c2++;
	      }
	    $c++;
	  }
      }

    return 1;
  }

sub checkAlert()
#Check to see if equipement in alert is part of this equipment group.
  {
    my ($this,$eGID,$alert)=@_;

    my $filters=$this->{info}[$eGID]->{filters};

    my $alertid=$alert->getID();
    $this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "checking to see if alertid $alertid is in equipmentgroup $eGID");

    #Get numExclude and numInclude
    my $numExclude=0;
    my $numInclude=0;
    foreach my $filter (@$filters)
      {
	if($filter->{included})
	  {
	    $numInclude++;
	  }
	else
	  {
	    $numExclude++;
	  }
      }

    #Go through filters
    my $ret=0;
    foreach my $ef (@$filters)
      {
	my $fms=$ef->{filterMatch};
	foreach my $fm (@$fms)
	  {
	    my $match=$this->checkMatch($fm,$alert);

	    if($match==1 && $ef->{included}==1)
	      {
		$ret=1;
	      }
	    elsif($match && !$ef->{included})
	      {
		$ret=0;
	      }
	
	    if($ret==1 && $numExclude==0)
	      {
		  $this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "Alertid $alertid is in equipmentgroup $eGID");
		  return 1
	      }
	    elsif(!$ret && !$numInclude)
	      {
		  $this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "Alertid $alertid is not in equipmentgroup $eGID");
		  return 0;
	      }

	    if($ef->{included})
	      {
		$numInclude--;
	      }
	    else
	      {
		$numExclude--;
	      }
	  }
      }

    if($ret==0) {
	$this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "Alertid $alertid is in equipmentgroup $eGID");
    } else {
	$this->{log}->printlog("EquipmentGroups","checkAlert",$Log::debugging, "Alertid $alertid is not in equipmentgroup $eGID");
    }

    return $ret;
  }

sub checkMatch()
  {
    my ($this,$fm,$alert)=@_;

    #Get correct info from alert
    my $info=$alert->getInfo($fm->{valuename});

    if($fm->{datatype}==$this->{datatype}{string}) {
	return $this->checkString($fm->{type},$fm->{value},$info);
    }
    elsif($fm->{datatype}==$this->{datatype}{int}) {
	return $this->checkInt($fm->{type},$fm->{value},$info);
    }
    elsif($fm->{datatype}==$this->{datatype}{ip}) {
	return $this->checkIP($fm->{type},$fm->{value},$info);
    }
    else {
	return $this->checkString($fm->{type},$fm->{value},$info);
    }

    return 0;
  }

sub checkString()
{
    my ($this,$type,$value,$str)=@_;
    my $match=0;

    if($value eq $str) {
	$match=1;
    }

    if($type==$this->{type}{eq}) {
	return $match;
    } else {
	return !$match;
    }
	
}

sub checkInt()
{
    my ($this,$type,$value,$int)=@_;
    if($type==$this->{type}{eq}) {
	if($int==$value) {
	    return 1;
	}	    
    }
    elsif($type==$this->{type}{more}) {
	if($int>$value) {
	    return 1;
	}	    
    }
    elsif($type==$this->{type}{moreeq}) {
	if($int>=$value) {
	    return 1;
	}	    
    }
    elsif($type==$this->{type}{less}) {
	if($int<$value) {
	    return 1;
	}	    
    }
    elsif($type==$this->{type}{lesseq}) {
	if($int<=$value) {
	    return 1;
	}	    
    }
    elsif($type==$this->{type}{ne}) {
	if($int!=$value) {
	    return 1;
	}	    
    }
    return 0;	
}


sub checkStringRegExp()
{
    my ($this,$type,$value,$name)=@_;
    
    my $match=0;

    if($name=~/$value/)
    {
	$match=1;
    }

    if($type==$this->{type}{eq})
    {
	return $match;
    }
    if($type==$this->{type}{nq})
    {
	return !$match;
    }

    return 0;
}

sub checkIP()
# Suports following formats:
# * - all ip addresses are valid
# 10.0.0.1,10.0.0.2,10.1.1.0/24 - multiple IP addresses can be
# specified using , to seperate them.
  {
    my ($this,$type,$value,$ipaddr)=@_;

    my @list=split ",",$value;

    my $match=0;

    my $ip1;
    my $ip2=new NetAddr::IP($ipaddr);

    foreach my $addr (@list)
    {
	if($addr=~/^\*$/)
	{
	    $match=1;
	}
	else
	{
	    $ip1=new NetAddr::IP($addr);
	    if($ip1->contains($ip2)) 
	    {
		$match=1;
	    }
	}
    }


    if($type==$this->{type}{eq})
    {
	return $match;
    }
    if($type==$this->{type}{nq})
    {
	return !$match;
    }
    
    return 0;
  }

1;
