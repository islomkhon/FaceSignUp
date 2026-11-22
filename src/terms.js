export const termsVersion = "terms-v6";

export const termsSections = [
  {
    title: "1. Acceptance of these Terms",
    paragraphs: [
      "These Terms of Service govern your use of FaceSignUp and its face-based sign-in features. By creating an account, you confirm that you have read and agree to these Terms.",
      "If you do not agree, do not create an account and do not use the face registration feature."
    ]
  },
  {
    title: "2. Eligibility and guardian consent",
    paragraphs: [
      "You must be legally able to enter into these Terms. If you are below the age required by applicable law, a parent or legal guardian must review and accept these Terms and provide any consent required for face-data processing.",
      "Do not register another person's face or create an account on their behalf without their valid authorization."
    ]
  },
  {
    title: "3. Account registration",
    paragraphs: [
      "You must provide a unique name or nickname, protect your password, and create one security question and answer. You are responsible for activity performed through your account.",
      "Account names, passwords, and security answers must not be shared. Notify the service operator promptly if you believe your account, password, or security answer has been compromised."
    ]
  },
  {
    title: "4. Face data and biometric processing",
    paragraphs: [
      "By registering, you agree that FaceSignUp may create and store an encrypted numerical face template and a small encrypted profile thumbnail so you can sign in, verify that the same person remains present during a scan, and allow authorized administrators to identify your account.",
      "The face template and profile thumbnail are used for authentication, account protection, administrator account management, and service security. Only the encrypted thumbnail is retained; the other raw camera frames are processed for verification and deleted after use. Profile thumbnails are available only to authenticated administrators.",
      "You may withdraw consent and delete your account and face template at any time through the account deletion feature or the operator's official support process. Deleting the account removes the associated face template, profile thumbnail, security answer, and active sessions."
    ]
  },
  {
    title: "5. Authentication limitations",
    paragraphs: [
      "Face comparison, movement checks, screen-light checks, password verification, and security-answer recovery checks are security signals. They do not guarantee that a device, camera stream, or network is uncompromised.",
      "The current implementation does not provide certified presentation-attack detection and must not be represented as a certified identity-proofing service."
    ]
  },
  {
    title: "6. Your security responsibilities",
    paragraphs: [
      "Use a private, adequately lit environment during face registration and sign-in. Do not use virtual cameras, injected video, another person's recording, or attempts to defeat the security checks.",
      "Use a unique account password, choose a security answer for password recovery that others cannot easily discover or guess, keep both private, and do not reuse your FaceSignUp password on other services."
    ]
  },
  {
    title: "7. Acceptable use",
    paragraphs: [
      "You may not attempt unauthorized access, interfere with the service, reverse engineer security controls, submit unlawful content, impersonate another person, or use the service where biometric authentication is prohibited by law.",
      "The operator may suspend or terminate access when reasonably necessary to protect users, the service, or legal compliance."
    ]
  },
  {
    title: "8. Availability and changes",
    paragraphs: [
      "The service may be changed, suspended, or discontinued. Security updates may require users to renew enrollment or change authentication details.",
      "Material changes to these Terms will be presented through the service. Continued use after an updated acceptance requirement means you accept the revised Terms."
    ]
  },
  {
    title: "9. Privacy and retention",
    paragraphs: [
      "Personal data is processed for account creation, authentication, security, recovery, and operational requirements. Data is retained only as long as reasonably necessary for those purposes or as required by law.",
      "Access is restricted, face templates and profile thumbnails are encrypted at rest, and passwords and security answers are stored as one-way hashes. A separate privacy notice may provide additional jurisdiction-specific information."
    ]
  },
  {
    title: "10. Disclaimers and limitation",
    paragraphs: [
      "The service is provided on an as-available basis to the extent permitted by law. The operator does not promise uninterrupted operation or that every attempted authentication will succeed.",
      "Nothing in these Terms excludes rights or liability that cannot lawfully be excluded. Liability limitations must be completed after review under the operator's governing law."
    ]
  },
  {
    title: "11. Governing terms and contact",
    paragraphs: [
      "The deployment operator must identify its legal entity, governing law, dispute process, and official contact channel before public launch.",
      "Where translated interface text differs from the English legal text, the English legal text should be treated as the authoritative version unless applicable law requires otherwise."
    ]
  }
];

export const termsByLocale = {
  en: termsSections
};

termsByLocale["zh-CN"] = [
  {
    title: "1. 接受条款",
    paragraphs: [
      "本服务条款适用于您对 FaceSignUp 及其人脸登录功能的使用。创建账户即表示您已阅读并同意本条款。",
      "如果您不同意，请不要创建账户，也不要使用人脸注册功能。"
    ]
  },
  {
    title: "2. 资格与监护人同意",
    paragraphs: [
      "您必须具备依法接受本条款的能力。如果您的年龄低于适用法律要求，父母或法定监护人必须审阅并接受本条款，并提供人脸数据处理所需的所有同意。",
      "未经他人有效授权，不得注册他人的人脸或代他人创建账户。"
    ]
  },
  {
    title: "3. 账户注册",
    paragraphs: [
      "您必须提供唯一的姓名或昵称、妥善保护密码，并创建一个安全问题及答案。您应对通过您账户进行的活动负责。",
      "不得共享账户名称、密码或安全答案。如果您认为账户、密码或安全答案已泄露，请立即通知服务运营方。"
    ]
  },
  {
    title: "4. 人脸数据与生物识别处理",
    paragraphs: [
      "注册即表示您同意 FaceSignUp 创建并保存加密的数值化人脸模板和一张小型加密账户照片，以便您登录、确认扫描过程中始终是同一人，并允许授权管理员识别您的账户。",
      "人脸模板和账户照片用于身份验证、账户保护、管理员账户管理和服务安全。系统仅长期保存加密的缩略账户照片，其他原始摄像头画面只用于完成验证，并在使用后删除。账户照片仅可由已登录的管理员访问。",
      "您可以通过账户删除功能或运营方官方支持渠道，随时撤回同意并删除账户和人脸模板。删除账户将同时删除相关人脸模板、缩略账户照片、安全答案和有效会话。"
    ]
  },
  {
    title: "5. 身份验证限制",
    paragraphs: [
      "人脸比对、动作检查、屏幕光检查、密码验证及找回密码时的安全答案检查均为安全信号，不能保证设备、摄像头视频流或网络未遭入侵。",
      "当前实现不提供经认证的呈现攻击检测，不得将其描述为经认证的身份核验服务。"
    ]
  },
  {
    title: "6. 您的安全责任",
    paragraphs: [
      "进行人脸注册和登录时，请使用私密且光线充足的环境。不得使用虚拟摄像头、注入视频、他人录像或任何规避安全检查的行为。",
      "请设置唯一的账户密码；为找回密码选择一个他人难以发现或猜到的安全答案，并妥善保密；不要在其他服务中重复使用 FaceSignUp 密码。"
    ]
  },
  {
    title: "7. 可接受使用",
    paragraphs: [
      "您不得尝试未经授权的访问、干扰服务、逆向分析安全控制、提交违法内容、冒充他人，或在法律禁止生物识别身份验证的场景中使用本服务。",
      "运营方可在合理必要时暂停或终止访问，以保护用户、服务或遵守法律。"
    ]
  },
  {
    title: "8. 可用性与变更",
    paragraphs: [
      "服务可能被变更、暂停或停止。安全更新可能要求用户重新注册或更改身份验证信息。",
      "本条款的重大变更将通过服务展示。在更新后的接受要求生效后继续使用，即表示您接受修订后的条款。"
    ]
  },
  {
    title: "9. 隐私与保存期限",
    paragraphs: [
      "个人数据用于账户创建、身份验证、安全、找回和运营需求，仅在合理必要或法律要求的期限内保存。",
      "数据访问受到限制，人脸模板和缩略账户照片会加密保存，密码和安全答案以单向哈希形式保存。单独的隐私声明可能提供特定司法辖区的额外信息。"
    ]
  },
  {
    title: "10. 免责声明与责任限制",
    paragraphs: [
      "在法律允许的范围内，服务按现有可用状态提供。运营方不保证服务不会中断，也不保证每次身份验证都会成功。",
      "本条款不排除依法不得排除的权利或责任。责任限制必须在根据运营方适用法律审查后补充完整。"
    ]
  },
  {
    title: "11. 适用条款与联系方式",
    paragraphs: [
      "部署运营方必须在公开发布前明确其法律主体、适用法律、争议处理流程和官方联系方式。",
      "如果翻译文本与英文法律文本存在差异，除非适用法律另有要求，应以英文法律文本为准。"
    ]
  }
];

termsByLocale.ru = [
  {
    title: "1. Принятие Условий",
    paragraphs: [
      "Настоящие Условия обслуживания регулируют использование FaceSignUp и входа по лицу. Создавая аккаунт, вы подтверждаете, что прочитали и принимаете эти Условия.",
      "Если вы не согласны, не создавайте аккаунт и не используйте регистрацию лица."
    ]
  },
  {
    title: "2. Право на использование и согласие представителя",
    paragraphs: [
      "Вы должны иметь законное право принять эти Условия. Если вы не достигли требуемого законом возраста, родитель или законный представитель должен ознакомиться с Условиями, принять их и предоставить все необходимые согласия на обработку данных лица.",
      "Не регистрируйте лицо другого человека и не создавайте аккаунт от его имени без действительного разрешения."
    ]
  },
  {
    title: "3. Регистрация аккаунта",
    paragraphs: [
      "Необходимо указать уникальное имя или псевдоним, защищать пароль и создать один контрольный вопрос с ответом. Вы отвечаете за действия, выполненные через ваш аккаунт.",
      "Не сообщайте другим имя аккаунта, пароль или ответ на контрольный вопрос. Если вы считаете, что аккаунт, пароль или ответ скомпрометированы, немедленно сообщите оператору сервиса."
    ]
  },
  {
    title: "4. Данные лица и биометрическая обработка",
    paragraphs: [
      "Регистрируясь, вы разрешаете FaceSignUp создать и хранить зашифрованный числовой шаблон лица и небольшое зашифрованное фото профиля для входа, проверки того, что во время сканирования присутствует один и тот же человек, и распознавания аккаунта уполномоченными администраторами.",
      "Шаблон лица и фото профиля используются для аутентификации, защиты аккаунта, управления аккаунтами и безопасности сервиса. Постоянно сохраняется только зашифрованное уменьшенное фото профиля; остальные исходные кадры камеры обрабатываются для проверки и удаляются после использования. Фото профиля доступно только авторизованным администраторам.",
      "Вы можете отозвать согласие и удалить аккаунт и шаблон лица через функцию удаления или официальную службу поддержки. Удаление аккаунта также удаляет шаблон лица, уменьшенное фото профиля, контрольный ответ и активные сеансы."
    ]
  },
  {
    title: "5. Ограничения аутентификации",
    paragraphs: [
      "Сравнение лица, проверка движений, света экрана, пароля и контрольного ответа при восстановлении являются сигналами безопасности. Они не гарантируют, что устройство, видеопоток или сеть не скомпрометированы.",
      "Текущая реализация не обеспечивает сертифицированное обнаружение атак представления и не должна называться сертифицированной системой подтверждения личности."
    ]
  },
  {
    title: "6. Ваши обязанности по безопасности",
    paragraphs: [
      "При регистрации и входе используйте приватное и достаточно освещённое место. Запрещены виртуальные камеры, вставленное видео, записи другого человека и попытки обойти проверки безопасности.",
      "Используйте уникальный пароль аккаунта, выберите для восстановления ответ, который трудно узнать или угадать, храните оба секрета в тайне и не используйте пароль FaceSignUp в других сервисах."
    ]
  },
  {
    title: "7. Допустимое использование",
    paragraphs: [
      "Запрещается пытаться получить несанкционированный доступ, вмешиваться в работу сервиса, исследовать механизмы защиты, публиковать незаконный контент, выдавать себя за другого человека или использовать сервис там, где биометрическая аутентификация запрещена законом.",
      "Оператор может приостановить или прекратить доступ, если это разумно необходимо для защиты пользователей, сервиса или соблюдения закона."
    ]
  },
  {
    title: "8. Доступность и изменения",
    paragraphs: [
      "Сервис может изменяться, приостанавливаться или прекращать работу. Обновления безопасности могут потребовать повторной регистрации или изменения данных для входа.",
      "О существенных изменениях Условий будет сообщено через сервис. Продолжение использования после нового требования принятия означает согласие с изменёнными Условиями."
    ]
  },
  {
    title: "9. Конфиденциальность и хранение",
    paragraphs: [
      "Персональные данные обрабатываются для создания аккаунта, аутентификации, безопасности, восстановления и работы сервиса. Данные хранятся только разумно необходимый срок или в течение срока, требуемого законом.",
      "Доступ ограничен, шаблоны лица и уменьшенные фото профиля шифруются при хранении, а пароли и контрольные ответы хранятся в виде односторонних хешей. Отдельное уведомление о конфиденциальности может содержать дополнительные сведения для конкретной юрисдикции."
    ]
  },
  {
    title: "10. Отказ от гарантий и ограничение ответственности",
    paragraphs: [
      "В пределах, разрешённых законом, сервис предоставляется по мере доступности. Оператор не гарантирует непрерывную работу или успешную аутентификацию при каждой попытке.",
      "Условия не исключают права или ответственность, которые нельзя исключить по закону. Ограничения ответственности должны быть завершены после проверки по применимому праву оператора."
    ]
  },
  {
    title: "11. Применимые положения и контакт",
    paragraphs: [
      "Перед публичным запуском оператор должен указать юридическое лицо, применимое право, порядок разрешения споров и официальный канал связи.",
      "При расхождении перевода с английским юридическим текстом преимущественную силу имеет английский текст, если применимое право не требует иного."
    ]
  }
];

termsByLocale.es = [
  {
    title: "1. Aceptación de estos Términos",
    paragraphs: [
      "Estos Términos del servicio regulan el uso de FaceSignUp y del inicio de sesión facial. Al crear una cuenta, confirma que ha leído y acepta estos Términos.",
      "Si no está de acuerdo, no cree una cuenta ni utilice el registro facial."
    ]
  },
  {
    title: "2. Capacidad y consentimiento del tutor",
    paragraphs: [
      "Debe tener capacidad legal para aceptar estos Términos. Si no alcanza la edad exigida por la ley, su padre, madre o tutor legal deberá revisar y aceptar los Términos y otorgar los consentimientos necesarios para tratar los datos faciales.",
      "No registre el rostro de otra persona ni cree una cuenta en su nombre sin autorización válida."
    ]
  },
  {
    title: "3. Registro de la cuenta",
    paragraphs: [
      "Debe proporcionar un nombre o apodo único, proteger su contraseña y crear una pregunta de seguridad con su respuesta. Usted es responsable de la actividad realizada mediante su cuenta.",
      "No comparta el nombre de la cuenta, la contraseña ni la respuesta de seguridad. Informe de inmediato al operador si cree que su cuenta, contraseña o respuesta de seguridad han sido comprometidas."
    ]
  },
  {
    title: "4. Datos faciales y tratamiento biométrico",
    paragraphs: [
      "Al registrarse, acepta que FaceSignUp cree y almacene una plantilla facial numérica cifrada y una pequeña foto de perfil cifrada para iniciar sesión, verificar que la misma persona permanece presente durante un escaneo y permitir que administradores autorizados identifiquen su cuenta.",
      "La plantilla facial y la foto de perfil se utilizan para autenticación, protección de la cuenta, gestión administrativa y seguridad del servicio. Solo se conserva la miniatura cifrada; los demás fotogramas originales de la cámara se procesan para la verificación y se eliminan después de su uso. La foto de perfil solo está disponible para administradores autenticados.",
      "Puede retirar el consentimiento y eliminar su cuenta y plantilla facial mediante la función de eliminación o el canal oficial de soporte. La eliminación también borra la foto de perfil, la respuesta de seguridad y las sesiones activas."
    ]
  },
  {
    title: "5. Limitaciones de autenticación",
    paragraphs: [
      "La comparación facial, las pruebas de movimiento, la luz de pantalla, la contraseña y la respuesta de recuperación son señales de seguridad. No garantizan que el dispositivo, la cámara o la red no estén comprometidos.",
      "La implementación actual no ofrece detección certificada de ataques de presentación y no debe presentarse como un servicio certificado de verificación de identidad."
    ]
  },
  {
    title: "6. Sus responsabilidades de seguridad",
    paragraphs: [
      "Utilice un entorno privado y bien iluminado durante el registro y el inicio de sesión. No utilice cámaras virtuales, vídeo inyectado, grabaciones de otra persona ni intente eludir las comprobaciones de seguridad.",
      "Use una contraseña única para la cuenta, elija una respuesta de recuperación difícil de descubrir o adivinar, mantenga ambas en privado y no reutilice la contraseña de FaceSignUp en otros servicios."
    ]
  },
  {
    title: "7. Uso aceptable",
    paragraphs: [
      "No puede intentar accesos no autorizados, interferir con el servicio, eludir controles de seguridad, publicar contenido ilegal, suplantar a otra persona ni usar el servicio donde la autenticación biométrica esté prohibida.",
      "El operador podrá suspender o cancelar el acceso cuando sea razonablemente necesario para proteger a los usuarios, el servicio o cumplir la ley."
    ]
  },
  {
    title: "8. Disponibilidad y cambios",
    paragraphs: [
      "El servicio puede modificarse, suspenderse o descontinuarse. Las actualizaciones de seguridad pueden exigir un nuevo registro o cambios en los datos de autenticación.",
      "Los cambios importantes se mostrarán en el servicio. El uso continuado después de una nueva aceptación implica la aceptación de los Términos revisados."
    ]
  },
  {
    title: "9. Privacidad y conservación",
    paragraphs: [
      "Los datos personales se tratan para crear la cuenta, autenticar, proteger, recuperar y operar el servicio. Se conservan solo durante el tiempo razonablemente necesario o exigido por ley.",
      "El acceso es restringido, las plantillas faciales y las fotos de perfil están cifradas, y las contraseñas y respuestas de seguridad se almacenan como hashes unidireccionales. Un aviso de privacidad separado puede contener información adicional de la jurisdicción."
    ]
  },
  {
    title: "10. Exenciones y limitación de responsabilidad",
    paragraphs: [
      "En la medida permitida por la ley, el servicio se ofrece según disponibilidad. El operador no garantiza un funcionamiento ininterrumpido ni que toda autenticación tenga éxito.",
      "Estos Términos no excluyen derechos ni responsabilidades que no puedan excluirse legalmente. Los límites de responsabilidad deben completarse tras la revisión bajo la ley aplicable."
    ]
  },
  {
    title: "11. Ley aplicable y contacto",
    paragraphs: [
      "Antes del lanzamiento público, el operador debe indicar su entidad legal, ley aplicable, proceso de resolución de disputas y canal oficial de contacto.",
      "Si la traducción difiere del texto legal inglés, prevalecerá el texto inglés salvo que la ley aplicable exija otra cosa."
    ]
  }
];

termsByLocale.fr = [
  {
    title: "1. Acceptation des Conditions",
    paragraphs: [
      "Les présentes Conditions d’utilisation régissent l’utilisation de FaceSignUp et de la connexion faciale. En créant un compte, vous confirmez avoir lu et accepté ces Conditions.",
      "Si vous n’êtes pas d’accord, ne créez pas de compte et n’utilisez pas l’inscription faciale."
    ]
  },
  {
    title: "2. Capacité et accord du représentant légal",
    paragraphs: [
      "Vous devez avoir la capacité juridique d’accepter ces Conditions. Si vous n’avez pas l’âge légal requis, un parent ou représentant légal doit examiner et accepter les Conditions et fournir les consentements nécessaires au traitement des données faciales.",
      "N’enregistrez pas le visage d’une autre personne et ne créez pas de compte en son nom sans autorisation valable."
    ]
  },
  {
    title: "3. Création du compte",
    paragraphs: [
      "Vous devez fournir un nom ou surnom unique, protéger votre mot de passe et créer une question de sécurité avec sa réponse. Vous êtes responsable des activités effectuées avec votre compte.",
      "Ne partagez pas votre nom de compte, votre mot de passe ni votre réponse de sécurité. Informez immédiatement l’opérateur si vous pensez qu’ils ont été compromis."
    ]
  },
  {
    title: "4. Données faciales et traitement biométrique",
    paragraphs: [
      "En vous inscrivant, vous acceptez que FaceSignUp crée et conserve un modèle facial numérique chiffré et une petite photo de profil chiffrée afin de vous connecter, de vérifier que la même personne reste présente pendant un scan et de permettre aux administrateurs autorisés d’identifier votre compte.",
      "Le modèle facial et la photo de profil servent à l’authentification, à la protection du compte, à la gestion administrative et à la sécurité du service. Seule la miniature chiffrée est conservée ; les autres images brutes de la caméra servent à la vérification et sont supprimées après utilisation. La photo de profil n’est accessible qu’aux administrateurs authentifiés.",
      "Vous pouvez retirer votre consentement et supprimer le compte et le modèle facial via la fonction de suppression ou le support officiel. La suppression efface aussi la photo de profil, la réponse de sécurité et les sessions actives."
    ]
  },
  {
    title: "5. Limites de l’authentification",
    paragraphs: [
      "La comparaison faciale, les contrôles de mouvement, de lumière, de mot de passe et de réponse de récupération sont des signaux de sécurité. Ils ne garantissent pas que l’appareil, la caméra ou le réseau ne sont pas compromis.",
      "La version actuelle ne fournit pas de détection certifiée des attaques de présentation et ne doit pas être présentée comme un service certifié de vérification d’identité."
    ]
  },
  {
    title: "6. Vos responsabilités de sécurité",
    paragraphs: [
      "Utilisez un environnement privé et suffisamment éclairé. N’utilisez pas de caméra virtuelle, de vidéo injectée, d’enregistrement d’une autre personne ni de méthode visant à contourner les contrôles.",
      "Utilisez un mot de passe unique pour le compte, choisissez une réponse de récupération difficile à découvrir ou à deviner, gardez ces informations confidentielles et ne réutilisez pas votre mot de passe FaceSignUp ailleurs."
    ]
  },
  {
    title: "7. Utilisation acceptable",
    paragraphs: [
      "Vous ne devez pas tenter un accès non autorisé, perturber le service, contourner les protections, publier un contenu illégal, usurper l’identité d’autrui ou utiliser le service là où l’authentification biométrique est interdite.",
      "L’opérateur peut suspendre l’accès lorsque cela est raisonnablement nécessaire pour protéger les utilisateurs, le service ou respecter la loi."
    ]
  },
  {
    title: "8. Disponibilité et modifications",
    paragraphs: [
      "Le service peut être modifié, suspendu ou arrêté. Les mises à jour de sécurité peuvent imposer une nouvelle inscription ou de nouvelles informations d’authentification.",
      "Les changements importants seront présentés dans le service. Continuer à l’utiliser après une nouvelle acceptation vaut acceptation des Conditions révisées."
    ]
  },
  {
    title: "9. Confidentialité et conservation",
    paragraphs: [
      "Les données personnelles servent à créer le compte, authentifier, protéger, récupérer et exploiter le service. Elles sont conservées uniquement le temps raisonnablement nécessaire ou exigé par la loi.",
      "L’accès est limité, les modèles faciaux et les photos de profil sont chiffrés, et les mots de passe et réponses de sécurité sont stockés sous forme de hachages irréversibles. Une notice de confidentialité distincte peut ajouter des informations locales."
    ]
  },
  {
    title: "10. Garanties et responsabilité",
    paragraphs: [
      "Dans la mesure permise par la loi, le service est fourni selon disponibilité. L’opérateur ne garantit ni une disponibilité continue ni la réussite de chaque authentification.",
      "Ces Conditions n’excluent pas les droits ou responsabilités qui ne peuvent légalement être exclus. Les limites de responsabilité doivent être complétées après examen du droit applicable."
    ]
  },
  {
    title: "11. Droit applicable et contact",
    paragraphs: [
      "Avant le lancement public, l’opérateur doit indiquer son entité juridique, le droit applicable, le processus de règlement des litiges et son canal de contact officiel.",
      "En cas de divergence, la version juridique anglaise prévaut sauf si la loi applicable exige autre chose."
    ]
  }
];

termsByLocale.de = [
  {
    title: "1. Zustimmung zu diesen Bedingungen",
    paragraphs: [
      "Diese Nutzungsbedingungen regeln die Verwendung von FaceSignUp und der Gesichtsanmeldung. Mit der Kontoerstellung bestätigen Sie, diese Bedingungen gelesen zu haben und ihnen zuzustimmen.",
      "Wenn Sie nicht zustimmen, erstellen Sie kein Konto und verwenden Sie die Gesichtsregistrierung nicht."
    ]
  },
  {
    title: "2. Berechtigung und Zustimmung des Erziehungsberechtigten",
    paragraphs: [
      "Sie müssen rechtsfähig sein, diese Bedingungen zu akzeptieren. Minderjährige benötigen die Prüfung und Zustimmung eines Elternteils oder Erziehungsberechtigten sowie alle gesetzlich erforderlichen Einwilligungen zur Verarbeitung von Gesichtsdaten.",
      "Registrieren Sie nicht das Gesicht einer anderen Person und erstellen Sie ohne gültige Erlaubnis kein Konto für sie."
    ]
  },
  {
    title: "3. Kontoerstellung",
    paragraphs: [
      "Sie müssen einen eindeutigen Namen oder Spitznamen angeben, Ihr Passwort schützen und eine Sicherheitsfrage mit Antwort erstellen. Sie sind für Aktivitäten über Ihr Konto verantwortlich.",
      "Kontoname, Passwort und Sicherheitsantwort dürfen nicht weitergegeben werden. Informieren Sie den Betreiber sofort, wenn Sie eine Kompromittierung vermuten."
    ]
  },
  {
    title: "4. Gesichtsdaten und biometrische Verarbeitung",
    paragraphs: [
      "Mit der Registrierung stimmen Sie zu, dass FaceSignUp eine verschlüsselte numerische Gesichtsvorlage und ein kleines verschlüsseltes Profilfoto erstellt und speichert, damit Sie sich anmelden können, der Verbleib derselben Person während eines Scans geprüft wird und autorisierte Administratoren Ihr Konto erkennen können.",
      "Gesichtsvorlage und Profilfoto dienen der Authentifizierung, Kontosicherheit, administrativen Kontoverwaltung und Systemsicherheit. Nur das verschlüsselte Vorschaubild wird aufbewahrt; die übrigen Rohbilder der Kamera werden für die Prüfung verarbeitet und danach gelöscht. Das Profilfoto ist nur für angemeldete Administratoren zugänglich.",
      "Sie können die Einwilligung widerrufen und Konto sowie Gesichtsvorlage über die Löschfunktion oder den offiziellen Support löschen. Dabei werden auch das Profilfoto, die Sicherheitsantwort und aktive Sitzungen gelöscht."
    ]
  },
  {
    title: "5. Grenzen der Authentifizierung",
    paragraphs: [
      "Gesichtsvergleich, Bewegungs-, Licht-, Passwort- und Sicherheitsantwortprüfungen bei der Wiederherstellung sind Sicherheitssignale. Sie garantieren nicht, dass Gerät, Kamera oder Netzwerk unkompromittiert sind.",
      "Die aktuelle Umsetzung bietet keine zertifizierte Erkennung von Präsentationsangriffen und darf nicht als zertifizierte Identitätsprüfung bezeichnet werden."
    ]
  },
  {
    title: "6. Ihre Sicherheitspflichten",
    paragraphs: [
      "Verwenden Sie bei Registrierung und Anmeldung eine private, ausreichend beleuchtete Umgebung. Virtuelle Kameras, eingeschleuste Videos, Aufnahmen anderer Personen und Umgehungsversuche sind untersagt.",
      "Verwenden Sie ein einzigartiges Kontopasswort, wählen Sie eine Sicherheitsantwort für die Passwortwiederherstellung, die andere nicht leicht herausfinden oder erraten können, halten Sie beides geheim und verwenden Sie Ihr FaceSignUp-Passwort nicht für andere Dienste."
    ]
  },
  {
    title: "7. Zulässige Nutzung",
    paragraphs: [
      "Unzulässig sind unbefugter Zugriff, Störung des Dienstes, Umgehung von Sicherheitsmaßnahmen, rechtswidrige Inhalte, Identitätsmissbrauch und die Nutzung, wenn biometrische Authentifizierung gesetzlich verboten ist.",
      "Der Betreiber kann den Zugang sperren, wenn dies zum Schutz von Nutzern, Dienst oder gesetzlicher Pflichten erforderlich ist."
    ]
  },
  {
    title: "8. Verfügbarkeit und Änderungen",
    paragraphs: [
      "Der Dienst kann geändert, ausgesetzt oder eingestellt werden. Sicherheitsupdates können eine erneute Registrierung oder geänderte Anmeldedaten erfordern.",
      "Wesentliche Änderungen werden im Dienst angezeigt. Die weitere Nutzung nach einer erneuten Zustimmungsanforderung gilt als Zustimmung."
    ]
  },
  {
    title: "9. Datenschutz und Aufbewahrung",
    paragraphs: [
      "Personenbezogene Daten werden für Kontoerstellung, Authentifizierung, Sicherheit, Wiederherstellung und Betrieb verarbeitet und nur so lange wie erforderlich oder gesetzlich vorgeschrieben gespeichert.",
      "Der Zugriff ist beschränkt, Gesichtsvorlagen und Profilfotos sind verschlüsselt und Passwörter sowie Sicherheitsantworten werden als Einweg-Hashes gespeichert. Ein separater Datenschutzhinweis kann weitere lokale Informationen enthalten."
    ]
  },
  {
    title: "10. Gewährleistung und Haftung",
    paragraphs: [
      "Soweit gesetzlich zulässig, wird der Dienst nach Verfügbarkeit bereitgestellt. Der Betreiber garantiert weder ununterbrochenen Betrieb noch den Erfolg jeder Authentifizierung.",
      "Zwingende Rechte und Haftung bleiben unberührt. Haftungsbeschränkungen müssen nach Prüfung des anwendbaren Rechts vervollständigt werden."
    ]
  },
  {
    title: "11. Anwendbare Bedingungen und Kontakt",
    paragraphs: [
      "Vor dem öffentlichen Start muss der Betreiber Rechtsträger, anwendbares Recht, Streitbeilegung und offiziellen Kontakt angeben.",
      "Bei Abweichungen ist der englische Rechtstext maßgeblich, sofern zwingendes Recht nichts anderes verlangt."
    ]
  }
];

termsByLocale.ko = [
  {
    title: "1. 약관 동의",
    paragraphs: [
      "본 서비스 약관은 FaceSignUp 및 얼굴 로그인 기능의 이용을 규율합니다. 계정을 만들면 본 약관을 읽고 동의한 것으로 확인됩니다.",
      "동의하지 않는 경우 계정을 만들거나 얼굴 등록 기능을 사용하지 마세요."
    ]
  },
  {
    title: "2. 이용 자격과 보호자 동의",
    paragraphs: [
      "본 약관에 동의할 법적 능력이 있어야 합니다. 법정 연령 미만인 경우 부모 또는 법정 보호자가 약관을 검토하고 동의해야 하며 얼굴 데이터 처리에 필요한 모든 동의를 제공해야 합니다.",
      "다른 사람의 유효한 허가 없이 그 사람의 얼굴을 등록하거나 대신 계정을 만들 수 없습니다."
    ]
  },
  {
    title: "3. 계정 등록",
    paragraphs: [
      "고유한 이름 또는 별명을 제공하고, 비밀번호를 보호하며, 보안 질문 하나와 답변을 만들어야 합니다. 계정을 통한 활동에 대한 책임은 사용자에게 있습니다.",
      "계정 이름, 비밀번호 또는 보안 답변을 공유하지 마세요. 계정, 비밀번호 또는 보안 답변이 침해되었다고 의심되면 즉시 운영자에게 알리세요."
    ]
  },
  {
    title: "4. 얼굴 데이터와 생체 정보 처리",
    paragraphs: [
      "등록하면 FaceSignUp이 로그인, 스캔 중 동일 인물의 지속적 존재 확인 및 승인된 관리자의 계정 식별을 위해 암호화된 숫자 얼굴 템플릿과 작은 암호화 프로필 사진을 생성하고 저장하는 데 동의합니다.",
      "얼굴 템플릿과 프로필 사진은 인증, 계정 보호, 관리자 계정 관리 및 서비스 보안에 사용됩니다. 암호화된 축소 프로필 사진만 보관되며, 그 외 원본 카메라 화면은 검증 후 삭제됩니다. 프로필 사진은 인증된 관리자만 볼 수 있습니다.",
      "계정 삭제 기능이나 공식 지원 채널을 통해 언제든지 동의를 철회하고 계정과 얼굴 템플릿을 삭제할 수 있습니다. 계정을 삭제하면 프로필 사진, 보안 답변 및 활성 세션도 삭제됩니다."
    ]
  },
  {
    title: "5. 인증의 한계",
    paragraphs: [
      "얼굴 비교, 동작 확인, 화면 빛 확인, 비밀번호 검증 및 비밀번호 복구 시 보안 답변 확인은 보안 신호입니다. 기기, 카메라 스트림 또는 네트워크가 침해되지 않았음을 보장하지 않습니다.",
      "현재 구현은 인증된 프레젠테이션 공격 탐지를 제공하지 않으며 인증된 신원 확인 서비스로 표시해서는 안 됩니다."
    ]
  },
  {
    title: "6. 사용자의 보안 책임",
    paragraphs: [
      "등록과 로그인 시 사적이고 충분히 밝은 환경을 사용하세요. 가상 카메라, 주입된 영상, 다른 사람의 녹화 또는 보안 검사 우회를 사용할 수 없습니다.",
      "고유한 계정 비밀번호를 사용하고, 비밀번호 복구용으로 다른 사람이 쉽게 알거나 추측할 수 없는 보안 답변을 골라 둘 다 비밀로 유지하며, FaceSignUp 비밀번호를 다른 서비스에서 재사용하지 마세요."
    ]
  },
  {
    title: "7. 허용되는 사용",
    paragraphs: [
      "무단 접근, 서비스 방해, 보안 제어 우회, 불법 콘텐츠 제출, 타인 사칭 또는 생체 인증이 법적으로 금지된 곳에서의 사용을 금지합니다.",
      "운영자는 사용자, 서비스 또는 법적 준수를 보호하기 위해 합리적으로 필요한 경우 접근을 정지할 수 있습니다."
    ]
  },
  {
    title: "8. 서비스 제공과 변경",
    paragraphs: [
      "서비스는 변경, 중단 또는 종료될 수 있습니다. 보안 업데이트로 재등록 또는 인증 정보 변경이 필요할 수 있습니다.",
      "중요한 약관 변경은 서비스에서 안내됩니다. 갱신된 동의 요구 이후 계속 사용하면 개정 약관에 동의한 것으로 봅니다."
    ]
  },
  {
    title: "9. 개인정보와 보관",
    paragraphs: [
      "개인정보는 계정 생성, 인증, 보안, 복구 및 운영을 위해 처리되며 합리적으로 필요한 기간 또는 법에서 요구하는 기간 동안만 보관됩니다.",
      "접근이 제한되며 얼굴 템플릿과 프로필 사진은 암호화되고 비밀번호와 보안 답변은 일방향 해시로 저장됩니다. 별도의 개인정보 안내에서 지역별 정보를 제공할 수 있습니다."
    ]
  },
  {
    title: "10. 보증 및 책임 제한",
    paragraphs: [
      "법이 허용하는 범위에서 서비스는 이용 가능한 상태로 제공됩니다. 운영자는 중단 없는 운영이나 모든 인증의 성공을 보장하지 않습니다.",
      "법적으로 배제할 수 없는 권리와 책임은 제외되지 않습니다. 책임 제한은 적용 법률 검토 후 완성해야 합니다."
    ]
  },
  {
    title: "11. 준거 및 연락처",
    paragraphs: [
      "공개 출시 전 운영자는 법인명, 준거법, 분쟁 처리 절차 및 공식 연락 채널을 명시해야 합니다.",
      "번역과 영문 법률 문서가 다르면 강행 법규가 달리 요구하지 않는 한 영문이 우선합니다."
    ]
  }
];

termsByLocale.ja = [
  {
    title: "1. 本規約への同意",
    paragraphs: [
      "本利用規約は、FaceSignUp および顔認証ログイン機能の利用に適用されます。アカウントを作成すると、本規約を読み、同意したものとみなされます。",
      "同意しない場合は、アカウントを作成せず、顔登録機能を使用しないでください。"
    ]
  },
  {
    title: "2. 利用資格と保護者の同意",
    paragraphs: [
      "本規約に同意する法的能力が必要です。法定年齢に達していない場合、親権者または法定後見人が本規約を確認して同意し、顔データ処理に必要なすべての同意を与える必要があります。",
      "他者の有効な許可なく、その人の顔を登録したり、代理でアカウントを作成したりしないでください。"
    ]
  },
  {
    title: "3. アカウント登録",
    paragraphs: [
      "一意の名前またはニックネームを設定し、パスワードを保護し、秘密の質問と回答を1組作成してください。アカウントを通じて行われる活動については利用者が責任を負います。",
      "アカウント名、パスワード、秘密の質問の回答を共有しないでください。侵害を疑う場合は、直ちに運営者へ連絡してください。"
    ]
  },
  {
    title: "4. 顔データと生体情報の処理",
    paragraphs: [
      "登録により、FaceSignUp がログイン、スキャン中の同一人物の継続確認、および権限のある管理者によるアカウント識別のために、暗号化された数値顔テンプレートと小さな暗号化プロフィール写真を作成・保存することに同意します。",
      "顔テンプレートとプロフィール写真は、認証、アカウント保護、管理者によるアカウント管理、サービス保護に使用されます。暗号化された縮小プロフィール写真のみが保存され、その他の元のカメラ映像は検証後に削除されます。プロフィール写真は認証済みの管理者だけが閲覧できます。",
      "アカウント削除機能または公式サポートを通じて、いつでも同意を撤回し、アカウントと顔テンプレートを削除できます。削除時にはプロフィール写真、秘密の質問の回答、有効なセッションも削除されます。"
    ]
  },
  {
    title: "5. 認証の限界",
    paragraphs: [
      "顔比較、動作確認、画面光確認、パスワード検証、パスワード復元時の秘密の質問の回答確認はセキュリティ上の信号です。端末、カメラ映像、ネットワークが侵害されていないことを保証するものではありません。",
      "現在の実装は認証された提示攻撃検出を提供せず、認証済みの本人確認サービスとして表示してはなりません。"
    ]
  },
  {
    title: "6. 利用者のセキュリティ責任",
    paragraphs: [
      "登録とログイン時には、プライベートで十分に明るい環境を使用してください。仮想カメラ、注入映像、他人の録画、セキュリティ確認の回避を使用してはなりません。",
      "アカウント固有のパスワードを使用し、パスワード復元用に他人が簡単に見つけたり推測したりできない秘密の質問の回答を選び、両方を秘密に保ち、FaceSignUp のパスワードを他のサービスで再利用しないでください。"
    ]
  },
  {
    title: "7. 許容される利用",
    paragraphs: [
      "不正アクセス、サービス妨害、セキュリティ制御の回避、違法コンテンツの送信、他者へのなりすまし、生体認証が法律で禁止される用途での利用を禁止します。",
      "運営者は、利用者、サービス、法令遵守を保護するために合理的に必要な場合、アクセスを停止できます。"
    ]
  },
  {
    title: "8. 提供状況と変更",
    paragraphs: [
      "サービスは変更、停止、終了される場合があります。セキュリティ更新により再登録や認証情報の変更が必要になる場合があります。",
      "重要な規約変更はサービス上で提示されます。新しい同意要件の後に利用を続けると、改定規約に同意したものとみなされます。"
    ]
  },
  {
    title: "9. プライバシーと保存",
    paragraphs: [
      "個人データはアカウント作成、認証、セキュリティ、復元、運用のために処理され、合理的に必要な期間または法律で要求される期間だけ保存されます。",
      "アクセスは制限され、顔テンプレートとプロフィール写真は暗号化され、パスワードと秘密の質問の回答は一方向ハッシュで保存されます。別途のプライバシー通知で地域固有の情報を提供する場合があります。"
    ]
  },
  {
    title: "10. 保証と責任の制限",
    paragraphs: [
      "法律で認められる範囲で、サービスは利用可能な状態で提供されます。運営者は中断のない運用やすべての認証成功を保証しません。",
      "法律上排除できない権利や責任は除外されません。責任制限は適用法の確認後に完成させる必要があります。"
    ]
  },
  {
    title: "11. 準拠条件と連絡先",
    paragraphs: [
      "公開前に、運営者は法人名、準拠法、紛争処理手続、公式連絡先を明示する必要があります。",
      "翻訳と英語の法的文書が異なる場合、強行法規に別段の定めがない限り英語版が優先します。"
    ]
  }
];

termsByLocale.uz = [
  {
    title: "1. Ushbu shartlarga rozilik",
    paragraphs: [
      "Ushbu Foydalanish shartlari FaceSignUp va yuz orqali kirish xizmatidan foydalanishni tartibga soladi. Hisob yaratish orqali siz shartlarni o‘qiganingiz va ularga roziligingizni tasdiqlaysiz.",
      "Agar rozi bo‘lmasangiz, hisob yaratmang va yuzni ro‘yxatdan o‘tkazish xizmatidan foydalanmang."
    ]
  },
  {
    title: "2. Foydalanish huquqi va vasiy roziligi",
    paragraphs: [
      "Ushbu shartlarni qabul qilish uchun qonuniy huquq va layoqatga ega bo‘lishingiz kerak. Agar qonunda talab qilingan yoshga yetmagan bo‘lsangiz, ota-ona yoki qonuniy vasiy shartlarni ko‘rib chiqib qabul qilishi va yuz ma’lumotlarini qayta ishlash uchun zarur rozilikni berishi kerak.",
      "Boshqa shaxsning aniq ruxsatisiz uning yuzini ro‘yxatdan o‘tkazmang yoki uning nomidan hisob yaratmang."
    ]
  },
  {
    title: "3. Hisob yaratish",
    paragraphs: [
      "Noyob ism yoki taxallus kiritishingiz, parolingizni himoya qilishingiz hamda bitta xavfsizlik savoli va javobini yaratishingiz kerak. Hisobingiz orqali amalga oshirilgan harakatlar uchun siz javobgarsiz.",
      "Hisob nomi, parol yoki xavfsizlik javobini boshqalar bilan bo‘lishmang. Hisob, parol yoki xavfsizlik javobi buzilgan deb hisoblasangiz, xizmat operatoriga darhol xabar bering."
    ]
  },
  {
    title: "4. Yuz ma’lumotlari va biometrik qayta ishlash",
    paragraphs: [
      "Ro‘yxatdan o‘tish orqali siz FaceSignUp’ga kirish, skanerlash davomida bir xil odam qatnashayotganini tekshirish va vakolatli administratorlarga hisobingizni aniqlash imkonini berish uchun shifrlangan raqamli yuz shabloni va kichik shifrlangan profil rasmini yaratish va saqlashga ruxsat berasiz.",
      "Yuz shabloni va profil rasmi autentifikatsiya, hisobni himoya qilish, administrator tomonidan hisoblarni boshqarish va xizmat xavfsizligi uchun ishlatiladi. Faqat shifrlangan kichraytirilgan profil rasmi saqlanadi; kamera orqali olingan boshqa asl kadrlar tekshiruvdan so‘ng o‘chiriladi. Profil rasmini faqat tizimga kirgan administratorlar ko‘ra oladi.",
      "Hisobni o‘chirish funksiyasi yoki rasmiy yordam xizmati orqali istalgan vaqtda rozilikni qaytarib olib, hisob va yuz shablonini o‘chirishingiz mumkin. Hisob o‘chirilganda profil rasmi, xavfsizlik javobi va faol seanslar ham o‘chiriladi."
    ]
  },
  {
    title: "5. Autentifikatsiya cheklovlari",
    paragraphs: [
      "Yuzni solishtirish, harakat, ekran yorug‘ligi, parol va parolni tiklashdagi xavfsizlik javobini tekshirish xavfsizlik signallaridir. Ular qurilma, kamera oqimi yoki tarmoq buzilmaganiga kafolat bermaydi.",
      "Joriy tizim sertifikatlangan taqdimot hujumini aniqlashni taqdim etmaydi va uni sertifikatlangan shaxsni tasdiqlash xizmati deb ko‘rsatish mumkin emas."
    ]
  },
  {
    title: "6. Sizning xavfsizlik majburiyatlaringiz",
    paragraphs: [
      "Ro‘yxatdan o‘tish va kirishda xususiy va yaxshi yoritilgan muhitdan foydalaning. Virtual kamera, kiritilgan video, boshqa odamning yozuvi yoki xavfsizlik tekshiruvlarini chetlab o‘tishga urinish taqiqlanadi.",
      "Hisob uchun noyob paroldan foydalaning, parolni tiklash uchun boshqalar oson topa yoki taxmin qila olmaydigan xavfsizlik javobini tanlab, ikkalasini ham sir saqlang va FaceSignUp parolini boshqa xizmatlarda ishlatmang."
    ]
  },
  {
    title: "7. Maqbul foydalanish",
    paragraphs: [
      "Ruxsatsiz kirishga urinish, xizmatga xalaqit berish, xavfsizlik nazoratini chetlab o‘tish, noqonuniy kontent yuborish, boshqa shaxsni taqlid qilish yoki biometrik autentifikatsiya qonunan taqiqlangan joyda foydalanish mumkin emas.",
      "Operator foydalanuvchilar, xizmat yoki qonunchilikni himoya qilish uchun zarur bo‘lsa, kirishni to‘xtatib qo‘yishi yoki tugatishi mumkin."
    ]
  },
  {
    title: "8. Mavjudlik va o‘zgarishlar",
    paragraphs: [
      "Xizmat o‘zgartirilishi, to‘xtatilishi yoki yakunlanishi mumkin. Xavfsizlik yangilanishlari qayta ro‘yxatdan o‘tish yoki autentifikatsiya ma’lumotlarini o‘zgartirishni talab qilishi mumkin.",
      "Muhim shart o‘zgarishlari xizmat orqali ko‘rsatiladi. Yangilangan rozilik talabidan keyin foydalanishni davom ettirish o‘zgartirilgan shartlarga rozilik hisoblanadi."
    ]
  },
  {
    title: "9. Maxfiylik va saqlash",
    paragraphs: [
      "Shaxsiy ma’lumotlar hisob yaratish, autentifikatsiya, xavfsizlik, tiklash va xizmat faoliyati uchun qayta ishlanadi. Faqat oqilona zarur yoki qonunda talab qilingan muddat saqlanadi.",
      "Kirish cheklangan, yuz shablonlari va profil rasmlari shifrlangan, parollar va xavfsizlik javoblari bir tomonlama hash sifatida saqlanadi. Alohida maxfiylik xabarnomasi hududga xos qo‘shimcha ma’lumot berishi mumkin."
    ]
  },
  {
    title: "10. Kafolatlar va javobgarlik cheklovi",
    paragraphs: [
      "Qonun ruxsat bergan darajada xizmat mavjud holatida taqdim etiladi. Operator uzluksiz ishlash yoki har bir kirish urinishi muvaffaqiyatli bo‘lishiga kafolat bermaydi.",
      "Qonun bo‘yicha istisno qilib bo‘lmaydigan huquq va javobgarliklar saqlanadi. Javobgarlik cheklovlari operatorga tegishli qonunchilik asosida ko‘rib chiqilgandan keyin to‘ldirilishi kerak."
    ]
  },
  {
    title: "11. Qo‘llaniladigan shartlar va aloqa",
    paragraphs: [
      "Ommaviy ishga tushirishdan oldin operator yuridik shaxs nomi, qo‘llaniladigan qonun, nizolarni hal qilish tartibi va rasmiy aloqa kanalini ko‘rsatishi shart.",
      "Tarjima va ingliz tilidagi yuridik matn farq qilsa, amaldagi qonun boshqacha talab qilmasa, ingliz tili matni ustuvor hisoblanadi."
    ]
  }
];
