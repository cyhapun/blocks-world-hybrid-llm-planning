(define (problem bw_easy_006)
  (:domain blocks-world)

  (:objects
    a b c - block
  )

  (:init
    (on_table a)
    (on b a)
    (on c b)
    (clear c)
    (handempty)
  )

  (:goal
    (on_table c)
  )
)
