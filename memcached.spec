%define username   memcached
%define groupname  memcached
%bcond_without sasl
%bcond_with    seccomp
%bcond_without tls
%bcond_with tests

Name:          memcached
Version:       1.6.9
Release:       1
Epoch:         0
Summary:       A high-performance, distributed memory object caching system
License:       BSD
URL:           https://www.memcached.org/
Source0:       https://www.memcached.org/files/memcached-%{version}.tar.gz
Source1:       https://releases.pagure.org/memcached-selinux/memcached-selinux-1.0.2.tar.gz
Source2:       memcached.sysconfig

Patch0001:     memcached-unit.patch

BuildRequires: systemd perl-generators perl(Test::More) perl(Test::Harness)
BuildRequires: selinux-policy-devel libevent-devel make gcc

%{?with_sasl:BuildRequires: cyrus-sasl-devel}
%{?with_seccomp:BuildRequires: libseccomp-devel}
%{?with_tls:BuildRequires: openssl-devel}
Requires:           %{name}-help = %{version}-%{release}
Requires(pre):      shadow-utils
Requires:           (%{name}-selinux if selinux-policy-targeted)
%{?systemd_requires}
%description
memcached is a high-performance, distributed memory object caching
system, generic in nature, but intended for use in speeding up dynamic
web applications by alleviating database load.


%package       devel
Summary:       Header files for memcached development
Requires:      memcached = %{epoch}:%{version}-%{release}

%description devel
Install memcached-devel if you are developing C/C++ applications that require
access to the memcached binary include files.

%package       selinux
Summary:       Selinux policy module
License:       GPLv2
BuildRequires: selinux-policy
%{?selinux_requires}

%description selinux
Install memcached-selinux to ensure your system contains the latest SELinux policy
optimised for use with this version of memcached.

%package_help

%prep
%setup -q -b 1
%patch1 -p1 -b .unit

%build
%configure \
  %{?with_sasl: --enable-sasl --enable-sasl-pwdb} \
  %{?with_seccomp: --enable-seccomp} \
  %{?with_tls: --enable-tls}
make %{?_smp_mflags}
pushd ../memcached-selinux-1.0.2
make

%check
%{!?with_tests: exit 0}
rm -f t/whitespace.t
if [ `id -u` -ne 0 ]; then
  rm -f t/daemonize.t t/watcher.t t/expirations.t
fi
make test

%install
make install DESTDIR=%{buildroot} INSTALL="%{__install} -p"
rm -f %{buildroot}%{_bindir}/memcached-debug

install -D -p -m 755 scripts/memcached-tool     %{buildroot}%{_bindir}/memcached-tool
install -D -p -m 644 scripts/memcached-tool.1   %{buildroot}%{_mandir}/man1/memcached-tool.1
install -D -p -m 644 scripts/memcached.service  %{buildroot}%{_unitdir}/memcached.service
install -D -p -m 644 %{SOURCE2}                 %{buildroot}%{_sysconfdir}/sysconfig/memcached
cd ../memcached-selinux-1.0.2
install -d    %{buildroot}%{_datadir}/selinux/packages
install -d -p %{buildroot}%{_datadir}/selinux/devel/include/contrib
install -m 644 memcached.pp.bz2 %{buildroot}%{_datadir}/selinux/packages

%pre
getent group %{groupname} >/dev/null || groupadd -r %{groupname}
getent passwd %{username} >/dev/null || \
useradd -r -g %{groupname} -d /run/memcached \
    -s /sbin/nologin -c "Memcached daemon" %{username}
exit 0

%pre selinux
%selinux_relabel_pre -s targeted

%post
%systemd_post memcached.service

%post selinux
%selinux_modules_install -s targeted -p 200 %{_datadir}/selinux/packages/memcached.pp.bz2 &> /dev/null

%preun
%systemd_preun memcached.service

%postun
%systemd_postun_with_restart memcached.service

%postun selinux
if [ $1 -eq 0 ]; then
    %selinux_modules_uninstall -s targeted -p 200 memcached
fi

%posttrans selinux
%selinux_relabel_post -s targeted &> /dev/null

%files
%license COPYING
%config(noreplace) %{_sysconfdir}/sysconfig/memcached
%{_bindir}/memcached-tool
%{_bindir}/memcached
%{_unitdir}/memcached.service

%files devel
%{_includedir}/memcached/*

%files selinux
%license COPYING
%attr(0644,root,root) %{_datadir}/selinux/packages/memcached.pp.bz2
%ghost %{_sharedstatedir}/selinux/targeted/active/modules/200/memcached

%files help
%doc AUTHORS ChangeLog NEWS README.md doc/CONTRIBUTORS doc/*.txt
%{_mandir}/man1/memcached-tool.1*
%{_mandir}/man1/memcached.1*

%changelog
* Tue Jun 15 2021 liyanan <liyanan32@huawei.com> - 0:1.6.9-1
- update to 1.6.9

* Thu Jan 07 2021 wangyue<wangyue92@huawei.com> - 0:1.5.10-6
- fix CVE-2019-15026

* Fri Nov 06 2020 Ge Wang <wangge20@huawei.com> - 0:1.5.10-5
- set help package as memcached package's install require

* Thu Feb 27 2020 Lijin Yang <yanglijin@huawei.com> - 0:1.5.10-4
- fix install failed

* Fri Nov 29 2019 Lijin Yang <yanglijin@huawei.com> - 0:1.5.10-2
- init package

* Wed Feb 19 2020 yuxiangyang <yuxiangyang4@huawei.com> - 0:1.5.10-3
- fix package compile error
