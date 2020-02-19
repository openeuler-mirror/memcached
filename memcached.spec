%bcond_without sasl
%bcond_with    seccomp

Name:          memcached
Version:       1.5.10
Release:       3
Epoch:         0
Summary:       A high-performance, distributed memory object caching system
License:       BSD
URL:           https://www.memcached.org/
Source0:       https://www.memcached.org/files/memcached-%{version}.tar.gz
Source1:       https://pagure.io/memcached-selinux/raw/master/f/memcached-selinux-1.0.tar.gz
Source2:       memcached.sysconfig

Patch0001:     memcached-unit.patch
Patch6000:     CVE-2019-11596.patch

BuildRequires: systemd perl-generators perl(Test::More) perl(Test::Harness)
BuildRequires: selinux-policy-devel libevent-devel
%{?with_sasl:BuildRequires: cyrus-sasl-devel}
%{?with_seccomp:BuildRequires: libseccomp-devel}

Requires(pre):    shadow-utils
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd

%description
Memcached is a high-performance, distributed memory object caching system,
generic in nature, but originally intended for use in speeding up dynamic
web applications by alleviating database load.
You can think of it as a short-term memory for your applications.

%package       devel
Summary:       Header files for memcached development
Requires:      memcached = %{epoch}:%{version}-%{release}

%description devel
Header files for memcached development.

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
%autosetup -b 1 -p1
autoreconf -f -i

%build
%configure %{?with_sasl: --enable-sasl} %{?with_seccomp: --enable-seccomp}
%make_build

cd ../memcached-selinux-1.0
%make_build

%check
rm -f t/whitespace.t t/lru-maintainer.t

if [ `id -u` -ne 0 ]; then
  rm -f t/daemonize.t t/watcher.t t/expirations.t
fi
make test

%install
%make_install
rm -f %{buildroot}%{_bindir}/memcached-debug

install -D -p -m 755 scripts/memcached-tool     %{buildroot}%{_bindir}/memcached-tool
install -D -p -m 644 scripts/memcached-tool.1   %{buildroot}%{_mandir}/man1/memcached-tool.1
install -D -p -m 644 scripts/memcached.service  %{buildroot}%{_unitdir}/memcached.service
install -D -p -m 644 %{SOURCE2}                 %{buildroot}%{_sysconfdir}/sysconfig/memcached

cd ../memcached-selinux-1.0
install -d    %{buildroot}%{_datadir}/selinux/packages
install -d -p %{buildroot}%{_datadir}/selinux/devel/include/contrib
install -m 644 memcached.pp.bz2 %{buildroot}%{_datadir}/selinux/packages

%pre
getent group  memcached >/dev/null || groupadd -r memcached
getent passwd memcached >/dev/null || useradd -r -g memcached -d /run/memcached i \
                                      -s /sbin/nologin -c "Memcached daemon" memcached
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
* Fri Nov 29 2019 Lijin Yang <yanglijin@huawei.com> - 0:1.5.10-2
- init package

* Wed Feb 19 2020 yuxiangyang <yuxiangyang4@huawei.com> - 0:1.5.10-3
- fix package compile error
