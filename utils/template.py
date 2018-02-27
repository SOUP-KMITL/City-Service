class Page:
    class Field:
        content     = "content"
        first       = "first"
        last        = "last"
        sort        = "sort"
        size        = "size"
        total_pages = "totalPages"
        total_elems = "totalElements"
        num_elems   = "numberOfElements"
        curr_page   = "number"


class Service:
    class Field:
        id           = "_id"
        service_id   = "serviceId"
        service_name = "serviceName"
        description  = "description"
        thumbnail    = "thumbnail"
        swagger      = "swagger"
        sameple_data = "sampleData"
        app_link     = "appLink"
        video_link   = "videoLink"
        owner        = "owner"
        endpoint     = "endpoint"
        created_at   = "createdAt"
        updated_at   = "updatedAt"
        code         = "code"
        kind         = "kind"


class User:
    class Field:
        user_id = "userId"
        username = "userName"
        fname = "firstName"
        lname = "lastName"
        email = "email"
        token = "accessToken"
