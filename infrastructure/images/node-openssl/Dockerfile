FROM node@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5
ARG SOURCE_DATE_EPOCH
COPY *.deb SHA256SUMS /tmp/pinned-packages/
RUN cd /tmp/pinned-packages && sha256sum -c SHA256SUMS && DEBIAN_FRONTEND=noninteractive LC_ALL=C TZ=UTC dpkg -i *.deb && rm -rf /tmp/pinned-packages /var/log/apt/* /var/log/dpkg.log /var/cache/ldconfig/aux-cache && openssl version
