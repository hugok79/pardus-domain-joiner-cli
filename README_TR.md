# Pardus Domain Joiner CLI

**Pardus Domain Joiner CLI**, Pardus sistemlerinde bir etki alanına dahil olmak, etki alanından ayrılmak, etki alanı durumunu kontrol etmek, etki alanı bilgilerini görüntülemek için kullanılan bir komut satırı aracıdır.

CLI, etki alanı ile ilgili görevleri yönetmek için projeye dahil edilmiş özel olarak oluşturulmuş bir kütüphane kullanır.

## Komutlar 

```
pardus-domain-joiner-cli <command> [options]
```

---

### 1. Join

`sssd` veya `winbind` servisini kullanarak bir etki alanına dahil olun.

**Parametreler:**

* `service`: `sssd` veya `winbind` (hangi servis kullanılacak)
* `domain`: Domain adı (zorunlu)
* `user`: Kullanıcı adı (zorunlu)
* `-p --password`: Parola (isteğe bağlı, girilmezse program sorar)
* `--ou`: Organizational Unit (isteğe bağlı)
* `--workgroup`: Workgroup adı (winbind için opsiyonel)
* `--hostname`: Bilgisayar adı (isteğe bağlı, girilmezse hostname kullanılır)

**Örnek Kullanım:**

```bash
pardus-domain-joiner-cli join sssd example.com admin
```

Program parolayı soracaktır.

---

### 2. Leave

Dahil edilmiş olduğunuz etki alanından ayrılın.

**Parametreler:**

* `user`: Kullanıcı adı (zorunlu)
* `-p --password`: Parola (isteğe bağlı, sorulur)

**Örnek Kullanım:**

```bash
pardus-domain-joiner-cli leave admin
```

Program parolayı soracaktır.

---

### 3. Status

Etki alanının bağlantı durumunu kontrol edin.

**Örnek Kullanım:**

```bash
pardus-domain-joiner-cli status
```

---

### 4. Info

Belirtilen etki alanı için keşif bilgilerini görüntüler.

**Parametreler:**

* `domain`: Domain adı

**Örnek Kullanım:**

```bash
pardus-domain-joiner-cli info example.com
```

---

### 5. Change

Bilgisayarın ismini değiştirin.

**Parametreler:**

* `hostname`: Yeni hostname (zorunlu)

**Örnek Kullanım:**

```bash
pardus-domain-joiner-cli change newhostname
```

---

### 6. Version

CLI sürümünü görüntüle.

**Örnek Kullanım:**

```bash
pardus-domain-joiner-cli version
```

---

# Önemli Notlar

* Parola komut satırında verilmezse, program çalışırken güvenli şekilde parola ister.
* Komutları `root` yetkisiyle çalıştırmalısınız.
* `workgroup` sadece `winbind` servisinde kullanılır.

---